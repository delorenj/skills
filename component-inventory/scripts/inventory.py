#!/usr/bin/env python3
"""component-inventory — a component and service ledger that notices.

One CSV per repo, one row per billable or load-bearing component, refreshed
against live provider APIs. Read-only against every provider: this tool issues
describe/list/get calls and nothing else. It never creates, modifies or deletes
a resource, and it never writes a credential anywhere.

Subcommands
    list        print the ledger (optionally filtered)
    add         add or update one row
    set         change named fields on one existing row
    verify      re-read live provider APIs, refresh figures, stamp last_verified
    reconcile   sum the ledger against actual provider spend for a window
    audit       the thing that notices — findings, non-zero exit on an alarm

Credentials
    AWS         a profile that can assume into the target account; pass
                --aws-assume-role-arn / --aws-profile, or export credentials.
    Cloudflare  read from 1Password at verify time via `op read`.
    Twilio      same.
    Nothing is written to disk, logged, or echoed.
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import os
import shutil
import subprocess
import sys
from typing import Any

# --------------------------------------------------------------------------
# Schema
# --------------------------------------------------------------------------

COLUMNS = [
    "component_id",
    "provider",
    "account",
    "service",
    "resource_id",
    "region",
    "purpose",
    "owner",
    "status",
    "monthly_usd",
    "monthly_usd_max",
    "cost_basis",
    "unit_rate",
    "cost_source",
    "billing_key",
    "cost_window",
    "last_verified",
    "verified_by",
    "review_by",
    "introduced_by",
    "evidence",
    "depends_on",
    "teardown",
    "teardown_risk",
    "notes",
]

PROVIDERS = {
    "aws", "cloudflare", "twilio", "clerk", "gorilladesk",
    "openai", "resend", "1password", "homelab",
    # Added 2026-08-27 by the architecture-truth reconciliation. These are not
    # speculative: each was found wired into a running process and consuming a
    # real credential, and the ledger could not name any of them.
    #
    # `openrouter` matters twice over — the `openai` row above describes a
    # vendor this engagement does not use. The model traffic goes to OpenRouter
    # and always has; three processes share one key.
    "deepgram", "cartesia", "openrouter", "posthog", "hindsight",
}
OWNERS = {"automaticai", "client", "shared-operator-tooling", "undetermined"}
STATUSES = {"live", "rollback-only", "deprecated", "idle"}
BASES = {
    # a bill or a live meter said so
    "measured",
    # measured quantity x a published rate; no charge has posted yet
    "list-price",
    # inside a free allowance, with the allowance named
    "free-tier",
    # covered by a subscription this row does not itself pay for
    "included-in-plan",
    # a modelled figure, labelled as one, with its basis named
    "estimated",
    # the client's own contract; the figure is theirs, not ours
    "client-billed",
    # billed to someone else on a contract this engagement does not hold
    "out-of-scope",
}
RISKS = {"safe", "destructive", "blocked"}

# A zero on one of these bases was reasoned about. A zero on any other basis
# was assumed, and an assumed zero is how a $44/month cluster stayed invisible.
MEASURED_ZERO_BASES = {
    "measured", "free-tier", "included-in-plan", "client-billed", "out-of-scope",
}

# Ledger rows whose resource_id names a concept rather than something the
# provider will hand back from a list call.
NON_RESOURCE_SERVICES = {
    "vpc", "iam", "cost-allocation", "security-group", "rds-subnet-group",
    "kms-requests", "cloudwatch-metric",
}

# Only rows owned by us roll into the project total. A client-billed or
# operator-tooling row still carries its figure; it just does not become our
# number. This is the column that stops someone quoting the org bill as the
# engagement's cost.
BILLABLE_OWNER = "automaticai"

STALE_DAYS = 14

# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------


def today() -> str:
    return _dt.date.today().isoformat()


def run(cmd: list[str], env: dict[str, str] | None = None, timeout: int = 120,
        unset: tuple[str, ...] = ()) -> tuple[int, str, str]:
    """Run a command. Returns (rc, stdout, stderr). Never raises on non-zero."""
    merged = dict(os.environ)
    if env:
        merged.update(env)
    for k in unset:
        merged.pop(k, None)
    try:
        p = subprocess.run(
            cmd, capture_output=True, text=True, env=merged, timeout=timeout
        )
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "timed out"
    except FileNotFoundError as exc:
        return 127, "", str(exc)


def op_read(ref: str) -> str:
    """Resolve a 1Password reference. Returns "" when unavailable.

    The value is held in memory for the life of one API call and is never
    written to the ledger, to a log, or to stdout.
    """
    if not shutil.which("op"):
        return ""
    rc, out, _ = run(["op", "read", ref], timeout=45)
    return out.strip() if rc == 0 else ""


def money(x: float) -> str:
    return f"{x:.2f}"


def parse_money(s: str) -> float | None:
    s = (s or "").strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


# --------------------------------------------------------------------------
# Ledger IO
# --------------------------------------------------------------------------


def read_ledger(path: str) -> list[dict[str, str]]:
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        for c in COLUMNS:
            r.setdefault(c, "")
    return rows


def write_ledger(path: str, rows: list[dict[str, str]]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    rows = sorted(rows, key=lambda r: (r.get("provider", ""), r.get("component_id", "")))
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in COLUMNS})


def validate_row(r: dict[str, str]) -> list[str]:
    errs = []
    if not r.get("component_id"):
        errs.append("component_id is required")
    if r.get("provider") not in PROVIDERS:
        errs.append(f"provider must be one of {sorted(PROVIDERS)}")
    if r.get("owner") not in OWNERS:
        errs.append(f"owner must be one of {sorted(OWNERS)}")
    if r.get("status") not in STATUSES:
        errs.append(f"status must be one of {sorted(STATUSES)}")
    if r.get("cost_basis") not in BASES:
        errs.append(f"cost_basis must be one of {sorted(BASES)}")
    if r.get("teardown_risk") and r["teardown_risk"] not in RISKS:
        errs.append(f"teardown_risk must be one of {sorted(RISKS)}")
    for f in ("monthly_usd", "monthly_usd_max"):
        v = r.get(f, "")
        if v != "" and parse_money(v) is None:
            errs.append(f"{f} must be a number or empty")
    return errs


# --------------------------------------------------------------------------
# AWS access — read-only
# --------------------------------------------------------------------------


class Aws:
    """Read-only AWS access, optionally through an assumed role.

    Session credentials live in this object's private env dict and are passed
    to child processes only. They are never printed and never written.
    """

    def __init__(self, profile: str | None, role_arn: str | None, region: str):
        self.region = region
        self._env: dict[str, str] = {"AWS_DEFAULT_REGION": region}
        self._unset: tuple[str, ...] = ()
        self.ok = False
        self.identity = ""
        self.error = ""
        if role_arn:
            base = ["aws", "sts", "assume-role", "--role-arn", role_arn,
                    "--role-session-name", "component-inventory",
                    "--duration-seconds", "3600",
                    "--query", "Credentials.[AccessKeyId,SecretAccessKey,SessionToken]",
                    "--output", "text"]
            if profile:
                base += ["--profile", profile]
            rc, out, err = run(base, timeout=60)
            if rc != 0:
                self.error = err.strip()
                return
            parts = out.strip().split("\t")
            if len(parts) != 3:
                self.error = "assume-role returned an unexpected shape"
                return
            self._env.update({
                "AWS_ACCESS_KEY_ID": parts[0],
                "AWS_SECRET_ACCESS_KEY": parts[1],
                "AWS_SESSION_TOKEN": parts[2],
            })
            # A lingering AWS_PROFILE would outrank the session we just minted.
            self._unset = ("AWS_PROFILE",)
        elif profile:
            self._env["AWS_PROFILE"] = profile
        rc, out, err = self.cli(["sts", "get-caller-identity"])
        if rc != 0:
            self.error = err.strip()
            return
        try:
            self.identity = json.loads(out)["Account"]
        except Exception:
            self.identity = ""
        self.ok = True

    def cli(self, args: list[str], timeout: int = 120) -> tuple[int, str, str]:
        cmd = ["aws", *args, "--output", "json"]
        return run(cmd, env=dict(self._env), timeout=timeout, unset=self._unset)

    def env_for_child(self) -> tuple[dict[str, str], tuple[str, ...]]:
        return dict(self._env), self._unset

    def j(self, args: list[str], timeout: int = 120) -> Any:
        rc, out, _err = self.cli(args, timeout=timeout)
        if rc != 0:
            return None
        try:
            return json.loads(out) if out.strip() else None
        except json.JSONDecodeError:
            return None


# --------------------------------------------------------------------------
# verify — refresh live figures
# --------------------------------------------------------------------------

HOURS_PER_MONTH = 730.0


def keep(r: dict[str, str], field: str, value: str) -> None:
    """Write `value` only when it does not throw provenance away.

    A refresh must never make a row say less than it said before. Anything a
    person wrote and the API cannot regenerate survives the machine pass.
    """
    cur = (r.get(field) or "").strip()
    if not cur or len(value) > len(cur):
        r[field] = value


def verify_aws(rows: list[dict[str, str]], aws: Aws, stamp: str) -> list[str]:
    """Confirm each AWS row's resource still exists and refresh what is
    directly measurable. Returns human-readable notes about what changed."""
    log: list[str] = []

    live: dict[str, Any] = {}
    live["rds_instances"] = (aws.j(["rds", "describe-db-instances"]) or {}).get("DBInstances", [])
    live["rds_clusters"] = (aws.j(["rds", "describe-db-clusters"]) or {}).get("DBClusters", [])
    live["ecs_families"] = (aws.j(["ecs", "list-task-definition-families", "--status", "ACTIVE"]) or {}).get("families", [])
    live["ecr"] = (aws.j(["ecr", "describe-repositories"]) or {}).get("repositories", [])
    live["kms_aliases"] = (aws.j(["kms", "list-aliases"]) or {}).get("Aliases", [])
    live["log_groups"] = (aws.j(["logs", "describe-log-groups"]) or {}).get("logGroups", [])
    live["alarms"] = (aws.j(["cloudwatch", "describe-alarms"]) or {}).get("MetricAlarms", [])
    live["lambdas"] = (aws.j(["lambda", "list-functions"]) or {}).get("Functions", [])
    live["schedules"] = (aws.j(["scheduler", "list-schedules"]) or {}).get("Schedules", [])
    live["rules"] = (aws.j(["events", "list-rules"]) or {}).get("Rules", [])
    live["params"] = (aws.j(["ssm", "describe-parameters"]) or {}).get("Parameters", [])
    live["buckets"] = (aws.j(["s3api", "list-buckets"]) or {}).get("Buckets", [])
    live["addresses"] = (aws.j(["ec2", "describe-addresses"]) or {}).get("Addresses", [])
    live["sns"] = (aws.j(["sns", "list-topics"]) or {}).get("Topics", [])
    live["clusters"] = (aws.j(["ecs", "list-clusters"]) or {}).get("clusterArns", [])
    live["sched_groups"] = (aws.j(["scheduler", "list-schedule-groups"]) or {}).get("ScheduleGroups", [])

    ids = set()
    for i in live["rds_instances"]:
        ids.add(i["DBInstanceIdentifier"])
    for c in live["rds_clusters"]:
        ids.add(c["DBClusterIdentifier"])
    ids |= set(live["ecs_families"])
    ids |= {r["repositoryName"] for r in live["ecr"]}
    ids |= {a["AliasName"] for a in live["kms_aliases"]}
    ids |= {g["logGroupName"] for g in live["log_groups"]}
    ids |= {a["AlarmName"] for a in live["alarms"]}
    ids |= {f["FunctionName"] for f in live["lambdas"]}
    ids |= {s["Name"] for s in live["schedules"]}
    ids |= {r["Name"] for r in live["rules"]}
    ids |= {p["Name"] for p in live["params"]}
    ids |= {b["Name"] for b in live["buckets"]}
    ids |= {a["PublicIp"] for a in live["addresses"]}
    ids |= {t["TopicArn"].rsplit(":", 1)[-1] for t in live["sns"]}
    ids |= {a.rsplit("/", 1)[-1] for a in live["clusters"]}
    ids |= {g["Name"] for g in live["sched_groups"]}

    # --- per-row refresh -------------------------------------------------
    for r in rows:
        if r.get("provider") != "aws":
            continue
        rid = (r.get("resource_id") or "").strip()

        # RDS instance class -> Pricing API -> instance-hour line
        inst = next((i for i in live["rds_instances"] if i["DBInstanceIdentifier"] == rid), None)
        if inst and r.get("service") == "rds-instance":
            cls = inst["DBInstanceClass"]
            rate = aws_rds_instance_rate(aws, cls)
            if rate:
                r["monthly_usd"] = money(rate * HOURS_PER_MONTH)
                r["monthly_usd_max"] = r["monthly_usd"]
                r["unit_rate"] = f"${rate:.4f}/instance-hour"
                r["cost_basis"] = "list-price"
                r["cost_source"] = f"aws pricing get-products AmazonRDS {cls} Single-AZ PostgreSQL"
                log.append(f"{r['component_id']}: instance rate refreshed to ${rate:.4f}/hr")

        if inst and r.get("service") == "rds-storage":
            gb = float(inst.get("AllocatedStorage") or 0)
            rate = 0.115  # gp3, us-east-1
            r["monthly_usd"] = money(gb * rate)
            r["unit_rate"] = f"${rate}/GB-month x {gb:.0f} GiB"
            log.append(f"{r['component_id']}: storage refreshed to {gb:.0f} GiB")

        # Aurora Serverless v2 — the floor is what bites, so record both
        clus = next((c for c in live["rds_clusters"] if c["DBClusterIdentifier"] == rid), None)
        if clus and r.get("service") == "aurora-serverless-v2":
            cfg = clus.get("ServerlessV2ScalingConfiguration") or {}
            floor = float(cfg.get("MinCapacity", 0) or 0)
            acu_rate = 0.12
            worst = max(floor, 0.5) * acu_rate * HOURS_PER_MONTH
            r["monthly_usd_max"] = money(worst)
            r["unit_rate"] = (
                f"${acu_rate}/ACU-hour; floor {floor} ACU, ceiling "
                f"{cfg.get('MaxCapacity')} ACU, pause after "
                f"{cfg.get('SecondsUntilAutoPause')}s idle"
            )
            acu = aws_metric(aws, "AWS/RDS", "ServerlessDatabaseCapacity",
                             [("DBClusterIdentifier", rid)], "Average", hours=24)
            recent = aws_metric(aws, "AWS/RDS", "ServerlessDatabaseCapacity",
                                [("DBClusterIdentifier", rid)], "Average", hours=3)
            if acu is not None:
                # The trailing 24h is the figure of record: it is the
                # conservative direction, and a cluster that spiked yesterday
                # must not be reported at its quietest minute.
                r["monthly_usd"] = money(acu * acu_rate * HOURS_PER_MONTH)
                r["cost_basis"] = "measured"
                rec = "no datapoint" if recent is None else f"{recent:.4f} ACU"
                r["cost_source"] = (
                    "cloudwatch AWS/RDS ServerlessDatabaseCapacity: "
                    f"{acu:.4f} ACU average over the trailing 24h "
                    f"(the figure of record), {rec} over the trailing 3h; "
                    "Aurora:ServerlessV2Usage in Cost Explorer corroborates"
                )
                r["cost_window"] = "trailing 24h"
                log.append(
                    f"{r['component_id']}: {acu:.4f} ACU over 24h -> "
                    f"${float(r['monthly_usd']):.2f}/month; {rec} over 3h; "
                    f"worst case ${worst:.2f}"
                )

        # ECR storage from actual image bytes
        if r.get("service") == "ecr-repository" and rid:
            imgs = aws.j(["ecr", "describe-images", "--repository-name", rid])
            if imgs:
                total = sum(d.get("imageSizeInBytes", 0) for d in imgs.get("imageDetails", []))
                gb = total / 1e9
                r["monthly_usd"] = money(gb * 0.10)
                r["unit_rate"] = f"$0.10/GB-month x {gb:.4f} GB"
                r["cost_basis"] = "measured"
                r["cost_source"] = f"aws ecr describe-images --repository-name {rid}"
                log.append(f"{r['component_id']}: {gb:.4f} GB of images")

        # KMS keys carry a flat monthly fee ONLY when customer-managed.
        # AWS-managed keys (alias/aws/*) are free, and pricing them at $1 was
        # the first bug this tool's own verify pass surfaced against itself.
        if r.get("service") == "kms-key" and rid:
            alias = next((a for a in live["kms_aliases"] if a["AliasName"] == rid), None)
            if alias:
                meta = aws.j(["kms", "describe-key", "--key-id", rid]) or {}
                mgr = (meta.get("KeyMetadata") or {}).get("KeyManager", "")
                if mgr == "CUSTOMER":
                    r["monthly_usd"] = money(1.00)
                    r["monthly_usd_max"] = money(1.00)
                    r["unit_rate"] = "$1.00 per customer-managed key per month"
                    r["cost_basis"] = "measured"
                    r["cost_source"] = ("aws kms describe-key (KeyManager CUSTOMER) "
                                        "+ us-east-1-KMS-Keys in Cost Explorer")
                    log.append(f"{r['component_id']}: customer-managed key, $1.00/month")
                else:
                    r["monthly_usd"] = money(0.00)
                    r["monthly_usd_max"] = money(0.00)
                    r["cost_basis"] = "free-tier"
                    # An AWS-managed key has nothing to learn from the API that
                    # a curated row does not already say, and a verify pass that
                    # overwrites hand-written provenance with a shorter machine
                    # string loses information every time it runs. Only fill in
                    # what is empty.
                    keep(r, "unit_rate", "AWS-managed keys carry no monthly fee")
                    keep(r, "cost_source",
                         f"aws kms describe-key (KeyManager {mgr or 'AWS'})")

        # S3 storage from the live object inventory
        if r.get("service") == "s3-bucket" and rid:
            cenv, cunset = aws.env_for_child()
            rc, out, _ = run(["aws", "s3", "ls", f"s3://{rid}", "--recursive", "--summarize"],
                             env=cenv, unset=cunset, timeout=300)
            if rc == 0 and "Total Size:" in out:
                lines = out.splitlines()
                size = int(next(x for x in lines if "Total Size:" in x).split(":")[1])
                objs = int(next(x for x in lines if "Total Objects:" in x).split(":")[1])
                gb = size / 1e9
                r["unit_rate"] = f"$0.023/GB-month x {gb:.6f} GB ({objs} objects)"
                log.append(f"{r['component_id']}: {objs} objects, {size} bytes")

        if rid and rid not in ids and r.get("service") not in NON_RESOURCE_SERVICES:
            log.append(f"{r['component_id']}: resource {rid} was not found live")
            continue

        r["last_verified"] = stamp
        r["verified_by"] = "component-inventory verify --provider aws"

    # --- undeclared live resources --------------------------------------
    # This is the check that would have caught the Aurora overlap: a resource
    # that is alive in the account and named nowhere in the ledger. An id
    # mentioned in any field of any row counts as declared, so a row may own
    # a small set of sibling resources by naming them in its notes.
    haystack = "\n".join(
        " ".join(r.get(c, "") for c in COLUMNS)
        for r in rows if r.get("provider") == "aws"
    )
    undeclared = sorted(i for i in ids if i and i not in haystack)
    for u in undeclared:
        log.append(f"UNDECLARED: live AWS resource '{u}' is named nowhere in the ledger")
    if not undeclared:
        log.append(f"every one of the {len(ids)} live AWS resources found is named in the ledger")
    return log


def aws_rds_instance_rate(aws: Aws, cls: str) -> float | None:
    out = aws.j([
        "pricing", "get-products", "--region", "us-east-1",
        "--service-code", "AmazonRDS",
        "--filters",
        f"Type=TERM_MATCH,Field=instanceType,Value={cls}",
        "Type=TERM_MATCH,Field=databaseEngine,Value=PostgreSQL",
        "Type=TERM_MATCH,Field=deploymentOption,Value=Single-AZ",
        "Type=TERM_MATCH,Field=regionCode,Value=us-east-1",
    ])
    if not out or not out.get("PriceList"):
        return None
    try:
        p = json.loads(out["PriceList"][0])
        for term in p["terms"]["OnDemand"].values():
            for dim in term["priceDimensions"].values():
                return float(dim["pricePerUnit"]["USD"])
    except Exception:
        return None
    return None


def aws_metric(aws: Aws, ns: str, name: str, dims: list[tuple[str, str]],
               stat: str, hours: int = 24) -> float | None:
    end = _dt.datetime.now(_dt.UTC)
    start = end - _dt.timedelta(hours=hours)
    args = ["cloudwatch", "get-metric-statistics", "--namespace", ns,
            "--metric-name", name, "--start-time", start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "--end-time", end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "--period", str(hours * 3600), "--statistics", stat]
    if dims:
        args += ["--dimensions", *[f"Name={k},Value={v}" for k, v in dims]]
    out = aws.j(args)
    if not out or not out.get("Datapoints"):
        return None
    return float(out["Datapoints"][0][stat])


def verify_cloudflare(rows: list[dict[str, str]], stamp: str) -> list[str]:
    log: list[str] = []
    email = op_read("op://DeLoSecrets/Cloudflare/username")
    key = op_read("op://DeLoSecrets/Cloudflare/globalAPIToken")
    if not (email and key):
        log.append("cloudflare: no credential resolved from 1Password; rows left as they were")
        return log
    hdr = ["-H", f"X-Auth-Email: {email}", "-H", f"X-Auth-Key: {key}"]

    def cf(path: str) -> Any:
        rc, out, _ = run(["curl", "-s", "--max-time", "30",
                          f"https://api.cloudflare.com/client/v4/{path}", *hdr], timeout=45)
        if rc != 0:
            return None
        try:
            return json.loads(out).get("result")
        except json.JSONDecodeError:
            return None

    accounts = {r.get("account") for r in rows if r.get("provider") == "cloudflare" and r.get("account")}
    live_ids: set[str] = set()
    plan_price: dict[str, float] = {}
    for acc in accounts:
        for s in (cf(f"accounts/{acc}/subscriptions") or []):
            name = s.get("rate_plan", {}).get("public_name", "")
            price = float(s.get("price") or 0)
            plan_price[name] = price
            live_ids.add(name)
        for s in (cf(f"accounts/{acc}/workers/scripts") or []):
            live_ids.add(s["id"])
        for n in (cf(f"accounts/{acc}/storage/kv/namespaces?per_page=100") or []):
            live_ids.add(n["title"])
            live_ids.add(n["id"])
        for d in (cf(f"accounts/{acc}/d1/database") or []):
            live_ids.add(d["name"])
    # Only zones belonging to a declared account. A global Cloudflare key can
    # see every account the operator owns; sweeping all of them would drown
    # this engagement's ledger in other projects' objects.
    for z in (cf("zones?per_page=100") or []):
        if z.get("account", {}).get("id") in accounts:
            live_ids.add(z["name"])

    for r in rows:
        if r.get("provider") != "cloudflare":
            continue
        rid = (r.get("resource_id") or "").strip()
        if rid in plan_price:
            r["monthly_usd"] = money(plan_price[rid])
            r["cost_basis"] = "measured"
            r["cost_source"] = f"cloudflare GET accounts/{r.get('account')}/subscriptions"
            log.append(f"{r['component_id']}: subscription price ${plan_price[rid]:.2f}/month")
        if rid and rid not in live_ids:
            log.append(f"{r['component_id']}: cloudflare resource '{rid}' was not found live")
            continue
        r["last_verified"] = stamp
        r["verified_by"] = "component-inventory verify --provider cloudflare"

    haystack = "\n".join(
        " ".join(r.get(c, "") for c in COLUMNS)
        for r in rows if r.get("provider") == "cloudflare"
    )
    strays = sorted(i for i in live_ids if i and i not in haystack)
    if strays:
        # These share an account with this engagement but belong to other
        # projects. They are reported once, as neighbours, so the shared-plan
        # row above stays honest without burying this ledger's own findings.
        log.append(f"NEIGHBOURS: {len(strays)} object(s) share these Cloudflare "
                   f"accounts and sit outside this engagement's scope: "
                   + ", ".join(strays))
    else:
        log.append(f"every one of the {len(live_ids)} in-scope Cloudflare objects "
                   "is named in the ledger")
    return log


def verify_twilio(rows: list[dict[str, str]], stamp: str) -> list[str]:
    log: list[str] = []
    sid = op_read("op://DeLoSecrets/Twilio-Intelliforia/Live Credentials/accountSID")
    tok = op_read("op://DeLoSecrets/Twilio-Intelliforia/Live Credentials/authToken")
    if not (sid and tok):
        log.append("twilio: no credential resolved from 1Password; rows left as they were")
        return log

    def tw(path: str) -> Any:
        rc, out, _ = run(["curl", "-s", "--max-time", "30", "-u", f"{sid}:{tok}",
                          f"https://api.twilio.com/2010-04-01/Accounts/{sid}/{path}"], timeout=45)
        if rc != 0:
            return None
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            return None

    usage = tw("Usage/Records/ThisMonth.json?PageSize=200") or {}
    by_cat = {u["category"]: u for u in usage.get("usage_records", [])}
    balance = (tw("Balance.json") or {}).get("balance")

    for r in rows:
        if r.get("provider") != "twilio":
            continue
        cat = (r.get("resource_id") or "").strip()
        rec = by_cat.get(cat)
        if rec is not None:
            price = float(rec.get("price") or 0)
            r["monthly_usd"] = money(price)
            r["cost_basis"] = "measured"
            r["cost_source"] = f"twilio GET Usage/Records/ThisMonth category={cat}"
            r["cost_window"] = "current Twilio billing month"
            r["unit_rate"] = f"usage {rec.get('usage')} {rec.get('usage_unit')}"
            log.append(f"{r['component_id']}: ${price:.4f} this month ({cat})")
        r["last_verified"] = stamp
        r["verified_by"] = "component-inventory verify --provider twilio"
    if balance is not None:
        log.append(f"twilio: prepaid balance ${balance} — the account is pay-as-you-go")
    return log


# --------------------------------------------------------------------------
# reconcile
# --------------------------------------------------------------------------


def cmd_reconcile(args) -> int:
    rows = read_ledger(args.csv)
    aws = Aws(args.aws_profile, args.aws_assume_role_arn, args.aws_region)
    if not aws.ok:
        print(f"reconcile: could not reach AWS ({aws.error})", file=sys.stderr)
        return 2
    start, end = args.start, args.end
    filt = json.dumps({"Dimensions": {"Key": "LINKED_ACCOUNT", "Values": [args.aws_account]}}) \
        if args.aws_account else None
    cmd = ["ce", "get-cost-and-usage",
           "--time-period", f"Start={start},End={end}",
           "--granularity", "MONTHLY", "--metrics", "UnblendedCost",
           "--group-by", "Type=DIMENSION,Key=USAGE_TYPE"]
    if filt:
        cmd += ["--filter", filt]
    out = aws.j(cmd)
    if not out:
        print("reconcile: Cost Explorer returned nothing", file=sys.stderr)
        return 2
    groups = out["ResultsByTime"][0].get("Groups", [])
    actual = {g["Keys"][0]: float(g["Metrics"]["UnblendedCost"]["Amount"]) for g in groups}
    total = sum(actual.values())

    print(f"AWS actual spend, {start} .. {end}"
          + (f", account {args.aws_account}" if args.aws_account else ""))
    print(f"  {'usage type':<34} {'USD':>12}   owning ledger row")
    claimed = 0.0
    unclaimed: list[str] = []
    for k in sorted(actual, key=lambda k: -actual[k]):
        owner_rows = [r["component_id"] for r in rows
                      if k in [t.strip() for t in (r.get("billing_key") or "").split(";")]]
        owner = ", ".join(owner_rows) if owner_rows else "-- no row claims this line --"
        if owner_rows:
            claimed += actual[k]
        else:
            if actual[k] > 0:
                unclaimed.append(k)
        print(f"  {k:<34} {actual[k]:>12.6f}   {owner}")
    print(f"  {'TOTAL':<34} {total:>12.6f}")
    print()
    print(f"claimed by a ledger row : ${claimed:.6f}")
    print(f"unattributed            : ${total - claimed:.6f}")
    if unclaimed:
        print("unattributed nonzero usage types: " + ", ".join(unclaimed))

    # The converse check, and the one that matters more: a row that names a
    # billing key the provider has never posted is a figure with nothing
    # behind it. Silence on a bill is not the same as a zero on a bill.
    declared: dict[str, list[str]] = {}
    for r in rows:
        if r.get("provider") != "aws":
            continue
        for k in [t.strip() for t in (r.get("billing_key") or "").split(";") if t.strip()]:
            declared.setdefault(k, []).append(r["component_id"])
    absent = {k: v for k, v in declared.items() if k not in actual}
    if absent:
        print()
        print("declared billing keys with no line in this window:")
        for k in sorted(absent):
            print(f"  {k:<40} claimed by {', '.join(absent[k])}")
        print("  (these rows carry a figure the provider has not yet charged for)")

    ledger_total = sum(
        parse_money(r.get("monthly_usd", "")) or 0.0
        for r in rows if r.get("provider") == "aws" and r.get("owner") == BILLABLE_OWNER
    )
    ledger_max = sum(
        parse_money(r.get("monthly_usd_max", "")) or parse_money(r.get("monthly_usd", "")) or 0.0
        for r in rows if r.get("provider") == "aws" and r.get("owner") == BILLABLE_OWNER
    )
    print()
    print(f"ledger AWS forward run-rate : ${ledger_total:.2f}/month "
          f"(worst case ${ledger_max:.2f}/month)")
    print("A run-rate and a month-to-date figure are different quantities. They agree")
    print("only once every row has been live for the whole window; until then the")
    print("reconciliation that holds is the line-by-line attribution above.")
    return 0 if not unclaimed else 1


# --------------------------------------------------------------------------
# audit — the thing that notices
# --------------------------------------------------------------------------


def cmd_audit(args) -> int:
    rows = read_ledger(args.csv)
    findings: list[tuple[str, str]] = []

    def alarm(msg): findings.append(("ALARM", msg))
    def note(msg): findings.append(("NOTE ", msg))

    if not rows:
        print(f"audit: no ledger at {args.csv}", file=sys.stderr)
        return 2

    for r in rows:
        cid = r.get("component_id", "?")
        for e in validate_row(r):
            alarm(f"{cid}: {e}")

        # 1. a retired row that the provider still reports as alive
        if r.get("status") in ("rollback-only", "deprecated"):
            spend = parse_money(r.get("monthly_usd", "")) or 0.0
            worst = parse_money(r.get("monthly_usd_max", "")) or spend
            if worst > 1.00:
                alarm(f"{cid}: status={r['status']} yet it can still bill up to "
                      f"${worst:.2f}/month — decide whether it stays")
            elif worst > 0:
                note(f"{cid}: status={r['status']}, still billing up to "
                     f"${worst:.2f}/month — goes when its parent goes")
            if not r.get("review_by"):
                alarm(f"{cid}: status={r['status']} with no review_by date — "
                      "a retired component with no expiry never gets retired")

        # 2. a zero nobody measured. A list-price zero has a published rate and
        # a measured quantity behind it; an estimated or unsourced zero has
        # neither, and that is the shape of the figure that hid Aurora.
        spend = parse_money(r.get("monthly_usd", ""))
        if spend == 0.0 and (r.get("cost_basis") == "estimated"
                             or not (r.get("cost_source") or "").strip()):
            alarm(f"{cid}: reports $0.00 on a '{r.get('cost_basis')}' basis with no "
                  "source — a zero that was configured rather than measured is "
                  "exactly how a $44/month cluster stayed invisible")

        # 3. a cheap number that is conditional on something
        worst = parse_money(r.get("monthly_usd_max", ""))
        if spend is not None and worst is not None and worst >= 5.0 and worst >= 5 * max(spend, 0.01):
            note(f"{cid}: ${spend:.2f}/month today, ${worst:.2f}/month at its ceiling — "
                 "the low figure holds only while its condition holds")

        # 4. a "measured" figure with no bill line behind it
        if r.get("cost_basis") == "measured" and not r.get("billing_key"):
            alarm(f"{cid}: cost_basis=measured with no billing_key — nothing on a bill "
                  "corroborates this figure, so it cannot be reconciled")

        # 5. provenance
        if not r.get("introduced_by"):
            alarm(f"{cid}: no introduced_by — nothing says which decision created it")
        if not r.get("teardown"):
            alarm(f"{cid}: no teardown command recorded")

        # 6. staleness
        lv = r.get("last_verified", "")
        try:
            age = (_dt.date.today() - _dt.date.fromisoformat(lv)).days
            if age > args.stale_days:
                alarm(f"{cid}: last_verified {lv} is {age} days old")
        except ValueError:
            alarm(f"{cid}: last_verified is not a date")

        # 7. an expired review
        rb = r.get("review_by", "")
        if rb:
            try:
                if _dt.date.fromisoformat(rb) < _dt.date.today():
                    alarm(f"{cid}: review_by {rb} has passed — this row is overdue a decision")
            except ValueError:
                alarm(f"{cid}: review_by is not a date")

        # 8. an unowned cost
        if r.get("owner") == "undetermined":
            note(f"{cid}: owner is undetermined — somebody is paying for it")

    # 9. two live rows for the same job
    seen: dict[tuple[str, str], list[str]] = {}
    for r in rows:
        if r.get("status") != "live":
            continue
        k = (r.get("service", ""), r.get("purpose", ""))
        seen.setdefault(k, []).append(r.get("component_id", "?"))
    for (svc, purpose), ids in seen.items():
        if len(ids) > 1 and svc:
            alarm(f"two live rows serve the same job ({svc} / {purpose}): {', '.join(ids)}")

    billable = [r for r in rows if r.get("owner") == BILLABLE_OWNER]
    total = sum(parse_money(r.get("monthly_usd", "")) or 0.0 for r in billable)
    ceiling = sum(
        parse_money(r.get("monthly_usd_max", "")) or parse_money(r.get("monthly_usd", "")) or 0.0
        for r in billable
    )

    print(f"component-inventory audit — {args.csv}")
    print(f"rows: {len(rows)}   ours: {len(billable)}   "
          f"run-rate ${total:.2f}/month   ceiling ${ceiling:.2f}/month")
    print()
    if not findings:
        print("no findings.")
        return 0
    for level, msg in findings:
        print(f"  [{level}] {msg}")
    print()
    alarms = sum(1 for lv, _ in findings if lv == "ALARM")
    print(f"{alarms} alarm(s), {len(findings) - alarms} note(s)")
    return 1 if alarms else 0


# --------------------------------------------------------------------------
# list / add / set / verify entry points
# --------------------------------------------------------------------------


def cmd_list(args) -> int:
    rows = read_ledger(args.csv)
    for f in ("provider", "owner", "status"):
        v = getattr(args, f, None)
        if v and v != "all":
            rows = [r for r in rows if r.get(f) == v]
    w = max([len(r.get("component_id", "")) for r in rows] + [12])
    print(f"{'component_id':<{w}}  {'provider':<11} {'status':<13} "
          f"{'owner':<24} {'USD/mo':>8} {'max':>8}  basis")
    for r in rows:
        print(f"{r.get('component_id',''):<{w}}  {r.get('provider',''):<11} "
              f"{r.get('status',''):<13} {r.get('owner',''):<24} "
              f"{r.get('monthly_usd',''):>8} {r.get('monthly_usd_max',''):>8}  "
              f"{r.get('cost_basis','')}")
    billable = [r for r in rows if r.get("owner") == BILLABLE_OWNER]
    total = sum(parse_money(r.get("monthly_usd", "")) or 0.0 for r in billable)
    ceiling = sum(
        parse_money(r.get("monthly_usd_max", "")) or parse_money(r.get("monthly_usd", "")) or 0.0
        for r in billable
    )
    print()
    print(f"{len(rows)} row(s); {len(billable)} owned by us: "
          f"${total:.2f}/month, ceiling ${ceiling:.2f}/month")
    return 0


def cmd_add(args) -> int:
    rows = read_ledger(args.csv)
    new = dict.fromkeys(COLUMNS, "")
    for c in COLUMNS:
        v = getattr(args, c.replace("-", "_"), None)
        if v is not None:
            new[c] = v
    if not new["last_verified"]:
        new["last_verified"] = today()
    if not new["verified_by"]:
        new["verified_by"] = "component-inventory add"
    errs = validate_row(new)
    if errs:
        for e in errs:
            print(f"add: {e}", file=sys.stderr)
        return 2
    existing = next((r for r in rows if r["component_id"] == new["component_id"]), None)
    if existing and not args.force:
        print(f"add: {new['component_id']} already exists; pass --force to replace",
              file=sys.stderr)
        return 2
    if existing:
        rows.remove(existing)
    rows.append(new)
    write_ledger(args.csv, rows)
    print(f"added {new['component_id']} ({new['provider']}) to {args.csv}")
    return 0


def cmd_set(args) -> int:
    rows = read_ledger(args.csv)
    row = next((r for r in rows if r["component_id"] == args.id), None)
    if row is None:
        print(f"set: no row with component_id {args.id}", file=sys.stderr)
        return 2
    for pair in args.field:
        if "=" not in pair:
            print(f"set: expected col=value, got {pair}", file=sys.stderr)
            return 2
        k, v = pair.split("=", 1)
        if k not in COLUMNS:
            print(f"set: {k} is not a column", file=sys.stderr)
            return 2
        row[k] = v
    row["last_verified"] = today()
    row["verified_by"] = "component-inventory set"
    errs = validate_row(row)
    if errs:
        for e in errs:
            print(f"set: {e}", file=sys.stderr)
        return 2
    write_ledger(args.csv, rows)
    print(f"updated {args.id}")
    return 0


def cmd_verify(args) -> int:
    rows = read_ledger(args.csv)
    if not rows:
        print(f"verify: no ledger at {args.csv}", file=sys.stderr)
        return 2
    stamp = today()
    log: list[str] = []
    want = args.provider
    if want in ("all", "aws"):
        aws = Aws(args.aws_profile, args.aws_assume_role_arn, args.aws_region)
        if aws.ok:
            log.append(f"aws: authenticated to account {aws.identity}")
            log += verify_aws(rows, aws, stamp)
        else:
            log.append(f"aws: could not authenticate ({aws.error}); AWS rows left as they were")
    if want in ("all", "cloudflare"):
        log += verify_cloudflare(rows, stamp)
    if want in ("all", "twilio"):
        log += verify_twilio(rows, stamp)
    write_ledger(args.csv, rows)
    print(f"component-inventory verify — {args.csv} ({stamp})")
    for line in log:
        print(f"  {line}")
    print()
    return cmd_list(args)


# --------------------------------------------------------------------------


def main() -> int:
    p = argparse.ArgumentParser(prog="component-inventory", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--csv", default="devops/inventory/components.csv")
    sub = p.add_subparsers(dest="cmd", required=True)

    def aws_flags(sp):
        sp.add_argument("--aws-profile", default=os.environ.get("INVENTORY_AWS_PROFILE"))
        sp.add_argument("--aws-assume-role-arn",
                        default=os.environ.get("INVENTORY_AWS_ROLE_ARN"))
        sp.add_argument("--aws-region", default="us-east-1")
        sp.add_argument("--aws-account", default=os.environ.get("INVENTORY_AWS_ACCOUNT"))

    sp = sub.add_parser("list", help="print the ledger")
    sp.add_argument("--provider"); sp.add_argument("--owner"); sp.add_argument("--status")
    sp.set_defaults(func=cmd_list)

    sp = sub.add_parser("add", help="add or replace one row")
    for c in COLUMNS:
        sp.add_argument(f"--{c.replace('_', '-')}", dest=c)
    sp.add_argument("--force", action="store_true")
    sp.set_defaults(func=cmd_add)

    sp = sub.add_parser("set", help="change fields on one row")
    sp.add_argument("--id", required=True)
    sp.add_argument("--field", action="append", default=[], metavar="COL=VALUE")
    sp.set_defaults(func=cmd_set)

    sp = sub.add_parser("verify", help="refresh figures from live provider APIs")
    sp.add_argument("--provider", default="all",
                    choices=["all", "aws", "cloudflare", "twilio"])
    sp.add_argument("--owner"); sp.add_argument("--status")
    aws_flags(sp)
    sp.set_defaults(func=cmd_verify)

    sp = sub.add_parser("reconcile", help="ledger against actual provider spend")
    sp.add_argument("--start", default=_dt.date.today().replace(day=1).isoformat())
    sp.add_argument("--end", default=(_dt.date.today() + _dt.timedelta(days=1)).isoformat())
    aws_flags(sp)
    sp.set_defaults(func=cmd_reconcile)

    sp = sub.add_parser("audit", help="findings; non-zero exit on an alarm")
    sp.add_argument("--stale-days", type=int, default=STALE_DAYS)
    sp.set_defaults(func=cmd_audit)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
