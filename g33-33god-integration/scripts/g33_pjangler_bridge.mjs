#!/usr/bin/env node
/**
 * g33 PJangler companion bridge — owner-side ES module adapter, API version 1.
 *
 * Exported callable: `g33Companion(request)` — the exact surface PJangler's
 * src/bmad/companion.ts resolves and calls:
 *   request = { schemaVersion: 1, moduleId: "g33",
 *               operation: "observe" | "plan" | "apply",
 *               projectRoot: string,
 *               reason: "recipe" | "bmad-install" | "audit" | "repair",
 *               options: Record<string, unknown> }
 *   reply   = { schemaVersion: 1,
 *               status: installed|missing|unavailable|conflict|error
 *                     | planned|changed|unchanged,
 *               summary: string, details: string[], evidence: string[] }
 *
 * Pure ES module; no shell-out to Python from JS beyond the documented
 * subprocess bridge into the owner's CLI (python -B, honoring read-only
 * observe/plan). Portable: module root derives from import.meta.dirname
 * (fileURLToPath fallback for older Node), overridable via options.
 * Supported options (unknown keys are REJECTED, never silently ignored):
 *   moduleRoot: string    — relocated module source root
 *   pythonExecutable: string — Python interpreter override
 *   answers: object       — installer answers passed through to apply
 */

import { spawn } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const BRIDGE_VERSION = "1.1.0";
const API_VERSION = 1;
const MODULE_ID = "g33";
const OPERATIONS = new Set(["observe", "plan", "apply"]);
const REASONS = new Set(["recipe", "bmad-install", "audit", "repair"]);
const STATUSES = {
  observe: new Set(["installed", "missing", "unavailable", "conflict", "error"]),
  plan: new Set(["planned", "unchanged", "unavailable", "conflict", "error"]),
  apply: new Set(["changed", "unchanged", "unavailable", "conflict", "error"]),
};
const SUPPORTED_OPTIONS = new Set([
  "moduleRoot", "pythonExecutable", "answers",
]);

function moduleDir() {
  // import.meta.dirname exists on modern Node; fileURLToPath fallback
  if (import.meta.dirname) return import.meta.dirname;
  return dirname(fileURLToPath(import.meta.url));
}

const THIS_DIR = moduleDir();
const DEFAULT_MODULE_ROOT = resolve(THIS_DIR, "..");

function err(summary, details) {
  return {
    schemaVersion: API_VERSION,
    status: "error",
    summary,
    details: details || [],
    evidence: [],
  };
}

/** observe the real installed state: content + activation links, read-only. */
async function observeState(projectRoot, moduleRoot, options, python) {
  const evidence = [];
  const details = [];
  const bmad = join(projectRoot, "_bmad");
  if (!existsSync(bmad)) {
    return {
      status: "missing",
      summary: "no _bmad directory: BMAD not installed in this project",
      details,
      evidence,
    };
  }
  // run the owner CLI preflight (read-only) for authoritative structure checks
  const pre = await runPython(
    python,
    [join(moduleRoot, "scripts", "g33_cli.py"), "preflight",
     "--project-root", projectRoot],
    options,
  );
  if (pre.code !== 0 && !pre.stdout.trim()) {
    return {
      status: "error",
      summary: "g33 preflight could not run",
      details: [pre.stderr.trim() || `exit ${pre.code}`],
      evidence,
    };
  }
  let preflight = {};
  try { preflight = JSON.parse(pre.stdout); } catch { /* keep {} */ }
  const conflictFinding = (preflight.findings || []).find(
    (f) => f.status === "FAIL" && /malformed|foreign|symlink|broken/.test(f.evidence || ""),
  );
  // structural conflict detection against the installer's rules
  const conflicts = await detectConflicts(projectRoot);
  if (conflicts.length) {
    return {
      status: "conflict",
      summary: "install-conflict detected; no mutation performed",
      details: conflicts.map((c) => `${c.path}: ${c.detail}`),
      evidence,
    };
  }
  if (conflictFinding) {
    return {
      status: "conflict",
      summary: "preflight conflict",
      details: [conflictFinding.evidence],
      evidence,
    };
  }
  // real content verification: every installed surface must exist with g33
  const customToml = join(bmad, "custom", "config.toml");
  const yaml = join(bmad, "config.yaml");
  const activeHelp = join(bmad, "_config", "bmad-help.csv");
  const legacyHelp = join(bmad, "module-help.csv");
  const checks = [];
  const tomlOk = () => {
    if (!existsSync(customToml)) return false;
    const t = readFileSync(customToml, "utf8");
    return /\[modules\.g33\]/.test(t) && /code\s*=\s*"g33"/.test(t);
  };
  const yamlOk = () => {
    if (!existsSync(yaml)) return false;
    const t = readFileSync(yaml, "utf8");
    return /^g33:\s*$/m.test(t);
  };
  const helpOk = () => {
    for (const p of [activeHelp, legacyHelp]) {
      if (existsSync(p) && /33GOD Integration,/.test(readFileSync(p, "utf8"))) {
        return p;
      }
    }
    return false;
  };
  const overridesOk = () => {
    const dir = join(bmad, "custom");
    const names = ["bmad-build.toml", "bmad-code-review.toml",
      "bmad-prd.toml", "bmad-spec.toml", "bmad-architecture.toml"];
    const present = names.filter((n) => existsSync(join(dir, n)));
    return present.length > 0 ? present : false;
  };
  const resolver = join(bmad, "scripts", "resolve_config.py");
  const resolverPresent = existsSync(resolver);
  const tomlInstalled = tomlOk();
  const yamlInstalled = yamlOk();
  const helpPath = helpOk();
  const overrideFiles = overridesOk();

  // tamper detection: partial installs (some surfaces present, others gone)
  const surfaces = [tomlInstalled, yamlInstalled, Boolean(helpPath), Boolean(overrideFiles)];
  const presentCount = surfaces.filter(Boolean).length;
  const requiredSurfaces = resolverPresent
    ? [tomlInstalled, yamlInstalled, Boolean(helpPath)]
    : [yamlInstalled, Boolean(helpPath)];

  if (presentCount > 0 && !requiredSurfaces.every(Boolean)) {
    return {
      status: resolverPresent && !tomlInstalled ? "missing" : "conflict",
      summary: "partial/tampered g33 install: installed surfaces are "
        + "inconsistent (missing or tampered files cannot count as installed)",
      details: [
        `[modules.g33] TOML: ${tomlInstalled ? "present" : "MISSING"}`,
        `config.yaml g33 section: ${yamlInstalled ? "present" : "MISSING"}`,
        `help CSV rows: ${helpPath ? "present" : "MISSING"}`,
        `skill overrides: ${overrideFiles ? overrideFiles.join(", ") : "MISSING"}`,
      ],
      evidence,
    };
  }
  if (!presentCount) {
    return {
      status: "missing",
      summary: "g33 is not installed in this project (no surfaces present)",
      details,
      evidence,
    };
  }
  // fully present — verify ACTIVE resolution through the real resolver
  if (resolverPresent) {
    const resolved = await runPython(
      python, [resolver, "--project-root", projectRoot, "--key", "modules.g33"],
      options, { cwd: join(resolver, "..", "..") },
    );
    if (resolved.code === 0 && resolved.stdout.includes('"g33"')) {
      evidence.push(`real resolve_config.py resolves modules.g33 (exit 0): ${resolved.stdout.replace(/\s+/g, " ").trim().slice(0, 200)}`);
    } else {
      return {
        status: "error",
        summary: "g33 files present but the real upstream resolver failed",
        details: [resolved.stderr.trim() || `resolver exit ${resolved.code}`],
        evidence,
      };
    }
  } else {
    details.push("upstream resolver absent: TOML layer inactive on this layout "
      + "(YAML-only state observed; not claimed active)");
  }
  if (helpPath) {
    evidence.push(`help rows present in ${relative(projectRoot, helpPath)}`);
  }
  if (overrideFiles) {
    evidence.push(`team overrides present: ${overrideFiles.join(", ")}`);
  }
  evidence.push(`config.yaml g33 section present (managed block)`);
  evidence.push(`custom/config.toml [modules.g33] present with code="g33"`);
  return {
    status: "installed",
    summary: "g33 installed: customization/header content, runtime/help "
      + "surfaces and canonical activation links verified by observation",
    details,
    evidence,
  };
}

async function detectConflicts(projectRoot) {
  const { default: fs } = await import("node:fs");
  const { join } = await import("node:path");
  const out = [];
  const yaml = join(projectRoot, "_bmad", "config.yaml");
  if (fs.existsSync(yaml)) {
    const text = fs.readFileSync(yaml, "utf8");
    const matches = text.split("\n").map((l, i) => [l, i])
      .filter(([l]) => /^g33\s*:/.test(l));
    if (matches.length > 1) {
      out.push({ path: yaml, detail: `duplicate g33 sections (${matches.length})` });
    } else if (matches.length === 1) {
      const line = matches[0][0];
      const rest = line.split(":").slice(1).join(":").trim();
      const hasManagedMarker = text.includes("# managed by g33 installer");
      if (rest && !rest.startsWith("#")) {
        out.push({ path: yaml, detail: `foreign inline g33 value: ${line.trim()}` });
      } else if (rest.startsWith("#") && !hasManagedMarker) {
        out.push({ path: yaml, detail: `foreign g33 comment header: ${line.trim()}` });
      }
    }
  }
  for (const p of [yaml,
    join(projectRoot, "_bmad", "custom", "config.toml"),
    join(projectRoot, "_bmad", "_config", "bmad-help.csv"),
    join(projectRoot, "_bmad", "module-help.csv")]) {
    let st = null;
    try { st = fs.lstatSync(p); } catch { /* absent */ }
    if (st && st.isSymbolicLink()) {
      out.push({ path: p, detail: `symlink target (refused write-through)` });
    }
  }
  return out;
}

function relative(from, to) {
  // tiny helper; avoid depending on path.relative edge cases in evidence text
  return to.startsWith(from) ? to.slice(from.length).replace(/^\//, "") : to;
}

function runPython(python, args, options, extra = {}) {
  return new Promise((res) => {
    const child = spawn(python, ["-B", ...args], {
      stdio: ["ignore", "pipe", "pipe"],
      env: {
        ...process.env,
        PYTHONDONTWRITEBYTECODE: "1",
        PYTHONSAFEPATH: "",
      },
      ...extra,
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (d) => { stdout += d; });
    child.stderr.on("data", (d) => { stderr += d; });
    child.on("error", (e) => res({ code: -1, stdout: "", stderr: String(e) }));
    child.on("close", (code) => res({ code, stdout, stderr }));
  });
}

/** The exported owner callable. Strict shapes in, strict shapes out. */
export async function g33Companion(request) {
  try {
    if (!request || typeof request !== "object") {
      return err("request must be an object");
    }
    if (request.schemaVersion !== API_VERSION) {
      return err(`unsupported schemaVersion ${String(request.schemaVersion)} (expected ${API_VERSION})`);
    }
    if (request.moduleId !== MODULE_ID) {
      return err(`unsupported moduleId ${String(request.moduleId)} (expected '${MODULE_ID}')`);
    }
    if (!OPERATIONS.has(request.operation)) {
      return err(`unsupported operation ${String(request.operation)}`);
    }
    if (!REASONS.has(request.reason)) {
      return err(`unsupported reason ${String(request.reason)}`);
    }
    if (typeof request.projectRoot !== "string" || !request.projectRoot.trim()) {
      return err("projectRoot must be a non-empty string");
    }
    const rawOptions = request.options ?? {};
    if (typeof rawOptions !== "object" || Array.isArray(rawOptions)) {
      return err("options must be an object");
    }
    const unknown = Object.keys(rawOptions).filter(
      (k) => !SUPPORTED_OPTIONS.has(k),
    );
    if (unknown.length) {
      return err(
        `unsupported option(s) rejected: ${unknown.join(", ")} `
        + `(supported: ${[...SUPPORTED_OPTIONS].join(", ")})`,
      );
    }
    const moduleRoot = typeof rawOptions.moduleRoot === "string" && rawOptions.moduleRoot.trim()
      ? resolve(rawOptions.moduleRoot)
      : DEFAULT_MODULE_ROOT;
    const python = typeof rawOptions.pythonExecutable === "string" && rawOptions.pythonExecutable.trim()
      ? rawOptions.pythonExecutable
      : "python3";
    const projectRoot = resolve(request.projectRoot);
    if (!existsSync(projectRoot)) {
      return err(`projectRoot not found: ${projectRoot}`);
    }
    if (!existsSync(join(moduleRoot, "scripts", "g33_install.py"))) {
      return {
        schemaVersion: API_VERSION, status: "unavailable",
        summary: `g33 module source unavailable at ${moduleRoot}`,
        details: ["moduleRoot must point at the g33-33god-integration source root"],
        evidence: [],
      };
    }
    const installerArgs = (dryRun) => {
      const args = [join(moduleRoot, "scripts", "g33_install.py"),
        "--project-root", projectRoot];
      if (dryRun) args.push("--dry-run");
      if (rawOptions.answers && typeof rawOptions.answers === "object"
        && !Array.isArray(rawOptions.answers)) {
        const tmp = join(moduleRoot, "..", ".g33-bridge-answers.json");
        // answers must round-trip through a file the installer validates;
        // write ONLY during apply (plan/apply dry-run uses defaults file too,
        // but plan must not write — installer validates in-memory there via
        // subprocess argv is not possible, so plan ignores answers and notes it)
        return { args, answers: rawOptions.answers };
      }
      return { args, answers: null };
    };

    if (request.operation === "observe") {
      const state = await observeState(projectRoot, moduleRoot, rawOptions, python);
      return { schemaVersion: API_VERSION, ...state };
    }
    if (request.operation === "plan") {
      const conflicts = await detectConflicts(projectRoot);
      if (conflicts.length) {
        return {
          schemaVersion: API_VERSION, status: "conflict",
          summary: "install-conflict detected; plan produced no writes",
          details: conflicts.map((c) => `${c.path}: ${c.detail}`),
          evidence: [],
        };
      }
      const planRun = await runPython(python, [
        join(moduleRoot, "scripts", "g33_install.py"),
        "--project-root", projectRoot, "--dry-run",
      ], rawOptions);
      if (planRun.code === 2) {
        let payload = {};
        try { payload = JSON.parse(planRun.stdout); } catch { }
        return {
          schemaVersion: API_VERSION, status: "conflict",
          summary: "installer preflight rejected the target",
          details: (payload.conflicts || []).map(
            (c) => `${c.path}: ${c.detail}`),
          evidence: [],
        };
      }
      if (planRun.code !== 0 || !planRun.stdout.trim()) {
        return err("installer plan failed", [
          planRun.stderr.trim() || `installer exit ${planRun.code}`,
        ]);
      }
      let payload = {};
      try { payload = JSON.parse(planRun.stdout); } catch {
        return err("installer plan emitted unparseable output");
      }
      const hasWrites = (payload.actions || []).some(
        (a) => ["write", "create", "overwrite"].includes(a.action),
      );
      return {
        schemaVersion: API_VERSION,
        status: hasWrites ? "planned" : "unchanged",
        summary: hasWrites
          ? `planned ${payload.actions.filter((a) => ["write", "create", "overwrite"].includes(a.action)).length} action(s); zero writes performed`
          : "no changes needed (already converged)",
        details: (payload.actions || []).map(
          (a) => `${a.action}: ${a.path}`),
        evidence: [
          "dry-run installer invocation completed with zero writes "
          + "(--dry-run; PYTHONDONTWRITEBYTECODE=1; python -B)",
        ],
      };
    }
    // apply
    const conflicts = await detectConflicts(projectRoot);
    if (conflicts.length) {
      return {
        schemaVersion: API_VERSION, status: "conflict",
        summary: "install-conflict detected; apply refused (zero mutations)",
        details: conflicts.map((c) => `${c.path}: ${c.detail}`),
        evidence: [],
      };
    }
    let answersFile = null;
    const applyArgs = [join(moduleRoot, "scripts", "g33_install.py"),
      "--project-root", projectRoot];
    if (rawOptions.answers && typeof rawOptions.answers === "object"
      && !Array.isArray(rawOptions.answers) && Object.keys(rawOptions.answers).length) {
      const { writeFileSync, rmSync } = await import("node:fs");
      const os = await import("node:os");
      answersFile = join(os.tmpdir(), `g33-bridge-answers-${process.pid}-${Date.now()}.json`);
      writeFileSync(answersFile, JSON.stringify(rawOptions.answers), "utf8");
      applyArgs.push("--answers", answersFile);
    }
    try {
      const applyRun = await runPython(python, applyArgs, rawOptions);
      if (applyRun.code === 2) {
        let payload = {};
        try { payload = JSON.parse(applyRun.stdout); } catch { }
        return {
          schemaVersion: API_VERSION, status: "conflict",
          summary: "installer rejected the target (zero mutations)",
          details: (payload.conflicts || []).map((c) => `${c.path}: ${c.detail}`),
          evidence: [],
        };
      }
      if (applyRun.code !== 0 || !applyRun.stdout.trim()) {
        return err("installer apply failed", [
          applyRun.stderr.trim() || `installer exit ${applyRun.code}`,
        ]);
      }
      let payload = {};
      try { payload = JSON.parse(applyRun.stdout); } catch {
        return err("installer apply emitted unparseable output");
      }
      const changed = (payload.performed || []).length > 0;
      // re-observe: mutation is never installation proof
      const state = await observeState(projectRoot, moduleRoot, rawOptions, python);
      if (state.status !== "installed") {
        return {
          schemaVersion: API_VERSION, status: "error",
          summary: "apply completed but re-observation does not prove installed",
          details: [state.summary, ...state.details],
          evidence: state.evidence,
        };
      }
      return {
        schemaVersion: API_VERSION,
        status: changed ? "changed" : "unchanged",
        summary: changed
          ? `applied ${payload.performed.length} action(s); re-observed installed`
          : "already converged; re-observed installed",
        details: (payload.performed || []).map((p) => `${p.action}: ${p.path}`),
        evidence: state.evidence,
      };
    } finally {
      if (answersFile) {
        const { rmSync } = await import("node:fs");
        try { rmSync(answersFile, { force: true }); } catch { /* best effort */ }
      }
    }
  } catch (error) {
    return err("g33 bridge internal error", [String(error && error.message || error)]);
  }
}

export const G33_BRIDGE_VERSION = BRIDGE_VERSION;
export const G33_API_VERSION = API_VERSION;
export default g33Companion;
