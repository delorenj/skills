#!/usr/bin/env python3
"""
domain_ctl.py - Manage Cloudflare Registrar domains and transfers for DeLoNET.
Reads credentials on-demand from 1Password (op://DeLoSecrets/Cloudflare/...).
"""

import argparse
import base64
import json
import os
import socket
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request


def get_credentials() -> tuple[str, str]:
    if os.getenv("CLOUDFLARE_API_KEY") and os.getenv("CLOUDFLARE_EMAIL"):
        return os.environ["CLOUDFLARE_EMAIL"], os.environ["CLOUDFLARE_API_KEY"]
    try:
        email = subprocess.run(
            ["op", "read", "op://DeLoSecrets/Cloudflare/username"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout.strip()
        key = subprocess.run(
            ["op", "read", "op://DeLoSecrets/Cloudflare/globalAPIToken"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout.strip()
        return email, key
    except Exception as e:
        sys.exit(f"Error fetching Cloudflare credentials from 1Password: {e}")


def cf_request(path: str, method: str = "GET", data: dict | None = None) -> dict:
    email, key = get_credentials()

    url = f"https://api.cloudflare.com/client/v4{path}"
    headers = {
        "X-Auth-Email": email,
        "X-Auth-Key": key,
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            return json.loads(err_body)
        except Exception:
            return {"success": False, "errors": [{"message": f"HTTP {e.code}: {err_body}"}]}
    except Exception as e:
        return {"success": False, "errors": [{"message": str(e)}]}


def get_account_id(account_name: str = "DeLoNET") -> str:
    res = cf_request("/accounts")
    if not res.get("success"):
        sys.exit(f"Failed to query Cloudflare accounts: {res.get('errors')}")
    accounts = res.get("result", [])
    for acc in accounts:
        if acc.get("name", "").lower() == account_name.lower():
            return acc["id"]
    if accounts:
        return accounts[0]["id"]
    sys.exit("No Cloudflare accounts found.")


def raw_whois(domain: str) -> str:
    tld = domain.split(".")[-1].lower()
    whois_servers = {
        "sh": "whois.nic.sh",
        "io": "whois.nic.io",
        "ai": "whois.nic.ai",
        "com": "whois.verisign-grs.com",
        "net": "whois.verisign-grs.com",
        "org": "whois.publicinterestregistry.org",
        "app": "whois.nic.google",
        "dev": "whois.nic.google",
    }
    server = whois_servers.get(tld, f"whois.nic.{tld}")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((server, 43))
        s.send(f"{domain}\r\n".encode("utf-8"))
        res = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            res += chunk
        s.close()
        return res.decode("utf-8", errors="ignore")
    except Exception as e:
        return f"WHOIS query failed: {e}"


def cmd_list(args):
    acc_id = get_account_id(args.account)
    res = cf_request(f"/accounts/{acc_id}/registrar/domains")
    if not res.get("success"):
        sys.exit(f"Failed to list domains: {res.get('errors')}")

    domains = res.get("result", [])
    print(f"\nCloudflare Registrar Domains ({args.account}):")
    print("-" * 80)
    print(f"{'Domain':<30} {'Expires':<15} {'AutoRenew':<10} {'Locked':<8} {'Registrar':<12}")
    print("-" * 80)
    for d in domains:
        name = d.get("name", "")
        expires = (d.get("expires_at") or "")[:10]
        auto = str(d.get("auto_renew", False))
        locked = str(d.get("locked", False))
        reg = d.get("current_registrar", "Cloudflare")
        print(f"{name:<30} {expires:<15} {auto:<10} {locked:<8} {reg:<12}")
    print("-" * 80)


def cmd_info(args):
    domain = args.domain.strip().lower()
    acc_id = get_account_id(args.account)
    res = cf_request(f"/accounts/{acc_id}/registrar/domains/{domain}")
    if not res.get("success"):
        print(f"Error querying Cloudflare registrar for {domain}: {res.get('errors')}")
    else:
        d = res.get("result", {})
        print(f"\nCloudflare Registrar Info for: {domain}")
        print("-" * 60)
        print(f"Current Registrar:      {d.get('current_registrar')}")
        print(f"Expires At:             {d.get('expires_at')}")
        print(f"Registry Statuses:      {d.get('registry_statuses')}")
        print(f"Auto Renew:             {d.get('auto_renew')}")
        print(f"Locked:                 {d.get('locked')}")
        print(f"Pending Transfer:       {d.get('pending_transfer')}")
        tc = d.get("transfer_conditions", {})
        print("Transfer Conditions:")
        for k, v in tc.items():
            print(f"  - {k}: {v}")

    print("\nLive Registry WHOIS:")
    print("-" * 60)
    whois_out = raw_whois(domain)
    filtered = [
        line
        for line in whois_out.splitlines()
        if any(
            k in line.lower()
            for k in [
                "status",
                "expiry",
                "expiration",
                "registrar:",
                "name server",
            ]
        )
    ]
    if filtered:
        print("\n".join(filtered))
    else:
        print(whois_out[:500])


def cmd_transfer_in(args):
    domain = args.domain.strip().lower()
    auth_code = args.auth_code.strip()
    acc_id = get_account_id(args.account)

    # Cloudflare requires base64-encoded auth code
    encoded_code = base64.b64encode(auth_code.encode("utf-8")).decode("utf-8")
    payload = {"auth_code": encoded_code}

    print(f"Initiating transfer-in for {domain} into account {acc_id}...")
    res = cf_request(
        f"/accounts/{acc_id}/registrar/registrations/{domain}/transfer-in",
        method="POST",
        data=payload,
    )
    if not res.get("success"):
        print(f"Transfer initiation failed: {json.dumps(res.get('errors'), indent=2)}")
        sys.exit(1)

    print("Transfer initiated successfully!")
    print(json.dumps(res.get("result"), indent=2))


def cmd_transfer_status(args):
    domain = args.domain.strip().lower()
    acc_id = get_account_id(args.account)

    res = cf_request(
        f"/accounts/{acc_id}/registrar/registrations/{domain}/transfer-in-status"
    )
    if not res.get("success"):
        print(f"Error querying transfer status: {json.dumps(res.get('errors'), indent=2)}")
    else:
        print(f"Transfer status for {domain}:")
        print(json.dumps(res.get("result"), indent=2))


def cmd_lock(args):
    domain = args.domain.strip().lower()
    acc_id = get_account_id(args.account)
    lock_val = not args.unlock
    payload = {"locked": lock_val}

    res = cf_request(
        f"/accounts/{acc_id}/registrar/domains/{domain}",
        method="PUT",
        data=payload,
    )
    if not res.get("success"):
        print(f"Failed to update lock status: {json.dumps(res.get('errors'), indent=2)}")
    else:
        print(f"Successfully set locked={lock_val} for {domain}.")


def main():
    parser = argparse.ArgumentParser(description="DeLoNET Domain Management CLI")
    parser.add_argument("--account", default="DeLoNET", help="Cloudflare account name")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # list
    subparsers.add_parser("list", help="List Cloudflare registrar domains")

    # info
    p_info = subparsers.add_parser("info", help="Get domain status and registry WHOIS")
    p_info.add_argument("domain", help="Domain name")

    # transfer-in
    p_trans = subparsers.add_parser("transfer-in", help="Initiate transfer into Cloudflare")
    p_trans.add_argument("domain", help="Domain name")
    p_trans.add_argument("auth_code", help="Registrar Auth/EPP code")

    # transfer-status
    p_status = subparsers.add_parser("transfer-status", help="Check transfer-in status")
    p_status.add_argument("domain", help="Domain name")

    # lock / unlock
    p_lock = subparsers.add_parser("lock", help="Lock domain registration")
    p_lock.add_argument("domain", help="Domain name")

    p_unlock = subparsers.add_parser("unlock", help="Unlock domain registration")
    p_unlock.add_argument("domain", help="Domain name")

    args = parser.parse_args()

    if args.command == "list":
        cmd_list(args)
    elif args.command == "info":
        cmd_info(args)
    elif args.command == "transfer-in":
        cmd_transfer_in(args)
    elif args.command == "transfer-status":
        cmd_transfer_status(args)
    elif args.command == "lock":
        args.unlock = False
        cmd_lock(args)
    elif args.command == "unlock":
        args.unlock = True
        cmd_lock(args)


if __name__ == "__main__":
    main()
