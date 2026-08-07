#!/usr/bin/env node
// One-command installer for the Last DS Mile Claude Code plugin.
// Zero dependencies (Node stdlib only) so `npx stamkavid/last-ds-mile`
// starts instantly with no install step of its own.
import { spawnSync } from "node:child_process";
import { accessSync, constants } from "node:fs";
import path from "node:path";

const REPO = "stamkavid/last-ds-mile";
const PLUGIN = "last-ds-mile";
const ON_WINDOWS = process.platform === "win32";

// Resolve `claude` to an absolute path ourselves rather than handing the bare name to
// a shell. On Windows the CLI is a `.cmd` shim, which is why this ever needed
// `shell: true` — but cmd.exe's search order includes the *current directory*, so
// `npx stamkavid/last-ds-mile` run inside a folder containing a stray `claude.bat`
// would execute that instead. Walking PATH ourselves removes both the shell and the
// hijack, and gives us a real answer to "is it installed?" before we spawn anything.
function resolveClaude() {
  const exts = ON_WINDOWS ? [".cmd", ".exe", ".bat"] : [""];
  const dirs = (process.env.PATH || "").split(path.delimiter).filter(Boolean);
  for (const dir of dirs) {
    for (const ext of exts) {
      const candidate = path.join(dir, `claude${ext}`);
      try {
        accessSync(candidate, constants.X_OK);
        return candidate;
      } catch {
        // not here, keep looking
      }
    }
  }
  return null;
}

const CLAUDE = resolveClaude();

function run(cmd, args) {
  return spawnSync(cmd, args, { stdio: "inherit", shell: false });
}

console.log("Last DS Mile — installing via Claude Code\n");

// `check.error` alone was a dead guard: under `shell: true` cmd.exe launches fine and
// reports a missing binary as a non-zero *status*, so on Windows — the platform most
// likely to hit it — this message never printed and the user got a raw
// "'claude' is not recognized" instead.
const check = CLAUDE
  ? spawnSync(CLAUDE, ["--version"], { stdio: "ignore", shell: false })
  : { error: new Error("not found"), status: null };
if (!CLAUDE || check.error || check.status !== 0) {
  console.error("Claude Code CLI (`claude`) was not found on your PATH.");
  console.error("Install it first: https://claude.com/claude-code");
  console.error("\nThen re-run: npx stamkavid/last-ds-mile");
  process.exit(1);
}

console.log(`1/2  claude plugin marketplace add ${REPO}`);
const addMarketplace = run(CLAUDE, ["plugin", "marketplace", "add", REPO]);
if (addMarketplace.status !== 0) {
  // Re-running the installer is a normal thing to do (upgrade, retry after fixing the
  // SSH issue below). If the marketplace is already registered, that step failing is
  // not a reason to abort the install.
  const already = run(CLAUDE, ["plugin", "marketplace", "list"]);
  if (already.status !== 0) {
    console.error("\nFailed to add the marketplace — see the error above.");
    process.exit(addMarketplace.status ?? 1);
  }
  console.log("\n     (marketplace already registered — continuing)");
}

console.log(`\n2/2  claude plugin install ${PLUGIN}`);
const install = run(CLAUDE, ["plugin", "install", PLUGIN]);
if (install.status !== 0) {
  console.error("\nFailed to install the plugin — see the error above.");
  console.error(
    "\nIf the error mentions 'Permission denied (publickey)' or an SSH clone\n" +
    "failure: `claude plugin install` clones over SSH, but you likely use\n" +
    "HTTPS-based GitHub auth (no SSH key registered) — the marketplace step\n" +
    "above falls back to HTTPS automatically, this one doesn't yet. Fix by\n" +
    "telling git to rewrite SSH GitHub URLs to HTTPS, then re-run this\n" +
    "installer (or just `claude plugin install last-ds-mile` again):\n\n" +
    '  git config --global url."https://github.com/".insteadOf git@github.com:\n'
  );
  process.exit(install.status ?? 1);
}

console.log("\nDone. Last DS Mile is installed.");
console.log("Open Claude Code in a project and run /ds-frame to start the pipeline,");
console.log("or /ds at any point to see the map and get routed to the next stage.");
