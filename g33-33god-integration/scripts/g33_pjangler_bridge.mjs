#!/usr/bin/env node
/** Owner-side PJangler companion callable, schemaVersion 1.
 * Options: moduleRoot, pythonExecutable; answers (plan/apply only).
 * Every request reports update-preservation unavailable: this seam supplies
 * no pre-updater capture/protect/restore/recovery protocol.
 */
import { spawn } from "node:child_process";
import { existsSync, readFileSync, mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { dirname, join, resolve, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { tmpdir } from "node:os";

const BRIDGE_VERSION = "1.1.0";
const API_VERSION = 1;
const OPERATIONS = new Set(["observe", "plan", "apply"]);
const REASONS = new Set(["recipe", "bmad-install", "audit", "repair"]);
const SUPPORTED_OPTIONS = new Set(["moduleRoot", "pythonExecutable", "answers"]);
const PRESERVATION = "update-preservation: unavailable; no supported pre-update capture/protection, post-update restore/reconcile/verify or failure recovery. Refuse upstream BMAD updates before mutation until the owning updater supplies that contract.";
const DEFAULT_MODULE_ROOT = resolve(import.meta.dirname || dirname(fileURLToPath(import.meta.url)), "..");
const SKILLS = ["bmad-build", "bmad-code-review", "bmad-prd", "bmad-spec", "bmad-architecture"];

function reply(status, summary, details = [], evidence = []) {
  return { schemaVersion: API_VERSION, status, summary, details: [...details, PRESERVATION], evidence };
}
function isObject(value) { return value !== null && typeof value === "object" && !Array.isArray(value); }
function runPython(python, args) {
  return new Promise((done) => {
    const child = spawn(python, ["-B", ...args], {
      stdio: ["ignore", "pipe", "pipe"],
      env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1", PYTHONSAFEPATH: "" },
    });
    let stdout = "", stderr = "";
    child.stdout.on("data", (data) => { stdout += data; });
    child.stderr.on("data", (data) => { stderr += data; });
    child.on("error", (error) => done({ code: -1, stdout: "", stderr: String(error) }));
    child.on("close", (code) => done({ code, stdout, stderr }));
  });
}

/** Both plan and apply use the SAME argv and answers, differing only in dry-run.
 * Answers exist only in a private temporary directory outside the project;
 * cleanup is synchronous and unconditional, including process-launch errors.
 */
async function runInstaller(projectRoot, moduleRoot, options, python, dryRun) {
  let temporary;
  try {
    const args = [join(moduleRoot, "scripts/g33_install.py"), "--project-root", projectRoot];
    if (dryRun) args.push("--dry-run");
    if (options.answers !== undefined) {
      temporary = mkdtempSync(join(tmpdir(), "g33-bridge-answers-"));
      const file = join(temporary, "answers.json");
      writeFileSync(file, JSON.stringify(options.answers), { encoding: "utf8", mode: 0o600 });
      args.push("--answers", file);
    }
    const run = await runPython(python, args);
    let payload;
    try { payload = JSON.parse(run.stdout); } catch { /* reported below */ }
    return { ...run, payload };
  } finally {
    if (temporary) rmSync(temporary, { recursive: true, force: true });
  }
}
function installerFailure(run) {
  if (run.code === 0 && run.payload?.status === "ok") return null;
  if (run.payload?.status === "conflict") {
    return reply("conflict", "installer preflight rejected the target; zero mutations",
      (run.payload.conflicts || []).map((c) => `${c.path}: ${c.detail}`));
  }
  return reply("error", "installer failed", [run.payload?.error || run.stderr.trim() || `installer exit ${run.code}`,
    ...(run.payload?.rollback ? [`rollback: ${run.payload.rollback.status}`, ...(run.payload.rollback.errors || [])] : [])]);
}

async function observeState(projectRoot, moduleRoot, options, python) {
  const bmad = join(projectRoot, "_bmad");
  if (!existsSync(bmad)) return reply("missing", "no _bmad directory: BMAD not installed in this project");
  // The owner installer is the single conflict authority, including ancestor
  // symlinks, malformed overrides, foreign sections and base config errors.
  const audit = await runInstaller(projectRoot, moduleRoot, options, python, true);
  const failed = installerFailure(audit);
  if (failed) return failed;
  if (!audit.payload.toml_active) {
    return reply("unavailable", "TOML runtime resolver absent: g33 is inactive on this YAML-only layout; PJAN-166 migration is outside this module", audit.payload.warnings || []);
  }
  const resolver = join(bmad, "scripts/resolve_config.py");
  const resolved = await runPython(python, [resolver, "--project-root", projectRoot, "--key", "modules.g33"]);
  let configuration;
  try { configuration = JSON.parse(resolved.stdout)["modules.g33"]; } catch { /* handled below */ }
  if (resolved.code !== 0) return reply("error", "real runtime resolver failed", [resolved.stderr.trim() || `resolver exit ${resolved.code}`]);
  if (!isObject(configuration) || configuration.code !== "g33") {
    return reply("missing", "real runtime resolver does not resolve modules.g33 with code g33");
  }
  const yaml = join(bmad, "config.yaml");
  const help = join(bmad, "_config/bmad-help.csv");
  // The installer owns parsed YAML identity and section-scoped ownership.
  // Raw header spelling is not a second, divergent observation authority.
  if (!existsSync(yaml) || audit.payload.yaml_namespace?.managed !== true || !existsSync(help)) {
    return reply("conflict", "partial/tampered g33 install: authoring/help surfaces are missing or inconsistent");
  }
  // The authoritative installer plan compares the complete normalized owned
  // CSV rows to canonical content. Any help repair action means observation
  // has found missing/tampered owned rows, including duplicates or args changes.
  const helpAction = (audit.payload.actions || []).find((action) =>
    resolve(action.path) === resolve(help));
  if (!helpAction || helpAction.action !== "already-present") {
    return reply("conflict", "owned g33 help registry rows are missing, duplicated or tampered; all canonical rows are required");
  }
  const evidence = [`real resolve_config.py resolves modules.g33 (exit 0): ${JSON.stringify(configuration)}`,
    `managed config.yaml g33 section present`, `help rows present in ${relative(projectRoot, help)}`];
  const customizationResolver = join(bmad, "scripts/resolve_customization.py");
  if (!existsSync(customizationResolver)) return reply("unavailable", "real customization resolver absent: installed override merge cannot be verified", [], evidence);
  let observed = 0;
  for (const name of SKILLS) {
    const skill = [".agents/skills", "skills", "_bmad/skills"].map((rel) => join(projectRoot, rel, name))
      .find((path) => existsSync(join(path, "customize.toml")) && existsSync(join(path, "SKILL.md")));
    if (!skill) continue;
    const override = join(bmad, "custom", `${name}.toml`);
    if (!existsSync(override)) return reply("conflict", `installed skill ${name} has no g33 team override`, [], evidence);
    const merged = await runPython(python, [customizationResolver, "--skill", skill,
      "--project-root", projectRoot, "--key", "workflow.activation_steps_prepend", "--key", "workflow.persistent_facts"]);
    let data;
    try { data = JSON.parse(merged.stdout); } catch { /* handled below */ }
    if (merged.code !== 0 || !isObject(data)) return reply("error", `real customization resolver failed for ${name}`, [merged.stderr.trim() || `resolver exit ${merged.code}`], evidence);
    const steps = data["workflow.activation_steps_prepend"];
    const facts = data["workflow.persistent_facts"];
    if (!Array.isArray(steps) || !steps.some((s) => typeof s === "string" && s.includes("g33"))
        || !Array.isArray(facts) || !facts.some((s) => typeof s === "string" && s.includes("g33"))) {
      return reply("conflict", `real customization merge for ${name} does not contain the g33 activation and persistent facts`, [], evidence);
    }
    observed++;
    evidence.push(`real resolve_customization.py merges g33 override for ${name} (exit 0): ${JSON.stringify(data)}`);
    evidence.push(`installed skill source readable at ${relative(projectRoot, skill)} (reference-only symlinks allowed)`);
  }
  if (!observed) return reply("unavailable", "no installed BMAD skill customization surface: g33 merge cannot be verified", [], evidence);
  return reply("installed", "g33 installed: real config and customization resolvers verify active runtime, authoring and help surfaces", [], evidence);
}

export async function g33Companion(request) {
  try {
    if (!isObject(request)) return reply("error", "request must be an object");
    if (request.schemaVersion !== API_VERSION) return reply("error", `unsupported schemaVersion ${String(request.schemaVersion)}`);
    if (request.moduleId !== "g33") return reply("error", `unsupported moduleId ${String(request.moduleId)}`);
    if (!OPERATIONS.has(request.operation)) return reply("error", `unsupported operation ${String(request.operation)}`);
    if (!REASONS.has(request.reason)) return reply("error", `unsupported reason ${String(request.reason)}`);
    if (typeof request.projectRoot !== "string" || !request.projectRoot.trim()) return reply("error", "projectRoot must be a non-empty string");
    const options = request.options ?? {};
    if (!isObject(options)) return reply("error", "options must be an object");
    const unknown = Object.keys(options).filter((key) => !SUPPORTED_OPTIONS.has(key));
    if (unknown.length) return reply("error", `unsupported option(s) rejected: ${unknown.join(", ")}`);
    for (const key of ["moduleRoot", "pythonExecutable"]) {
      if (options[key] !== undefined && (typeof options[key] !== "string" || !options[key].trim())) return reply("error", `${key} must be a non-empty string`);
    }
    if (options.answers !== undefined && !isObject(options.answers)) return reply("error", "answers must be an object");
    if (request.operation === "observe" && options.answers !== undefined) return reply("error", "answers apply only to plan/apply; observe reads installed configuration");
    const moduleRoot = options.moduleRoot ? resolve(options.moduleRoot) : DEFAULT_MODULE_ROOT;
    const python = options.pythonExecutable || "python3";
    const projectRoot = resolve(request.projectRoot);
    if (!existsSync(projectRoot)) return reply("error", `projectRoot not found: ${projectRoot}`);
    if (!existsSync(join(moduleRoot, "scripts/g33_install.py"))) return reply("unavailable", `g33 module source unavailable at ${moduleRoot}`);
    if (request.operation === "observe") return await observeState(projectRoot, moduleRoot, options, python);
    const planned = await runInstaller(projectRoot, moduleRoot, options, python, true);
    const failed = installerFailure(planned);
    if (failed) return failed;
    if (!planned.payload.toml_active) return reply("unavailable", "TOML runtime resolver absent: g33 is inactive on this YAML-only layout", planned.payload.warnings || []);
    if (request.operation === "plan") {
      const actions = planned.payload.actions || [];
      const count = actions.filter((a) => ["write", "create", "overwrite"].includes(a.action)).length;
      return reply(count ? "planned" : "unchanged", count ? `planned ${count} action(s); zero target writes performed` : "no changes needed (already converged)",
        actions.map((a) => `${a.action}: ${a.path}`), [
          "dry-run installer completed with zero target writes (--dry-run; python -B)",
          `validated effective installer answers: ${JSON.stringify(planned.payload.answers || {})}`,
        ]);
    }
    const applied = await runInstaller(projectRoot, moduleRoot, options, python, false);
    const applyFailure = installerFailure(applied);
    if (applyFailure) return applyFailure;
    const state = await observeState(projectRoot, moduleRoot, {}, python);
    if (state.status !== "installed") return reply(state.status === "unavailable" ? "unavailable" : "error",
      `apply completed; ${state.summary}`, state.details.filter((s) => s !== PRESERVATION), state.evidence);
    const count = (applied.payload.performed || []).length;
    return reply(count ? "changed" : "unchanged", count ? `applied ${count} action(s); re-observed installed` : "already converged; re-observed installed",
      (applied.payload.performed || []).map((a) => `${a.action}: ${a.path}`), state.evidence);
  } catch (error) {
    return reply("error", "g33 bridge internal error", [String(error?.message || error)]);
  }
}
export const G33_BRIDGE_VERSION = BRIDGE_VERSION;
export const G33_API_VERSION = API_VERSION;
export default g33Companion;
