#!/usr/bin/env node
// One-command installer for the Last DS Mile Claude Code plugin.
// Zero dependencies (Node stdlib only) so `npx github:stamkavid/last-ds-mile`
// starts instantly with no install step of its own.
import { spawnSync } from "node:child_process";

const REPO = "stamkavid/last-ds-mile";
const PLUGIN = "last-ds-mile";
const ON_WINDOWS = process.platform === "win32";

function run(cmd, args) {
  return spawnSync(cmd, args, { stdio: "inherit", shell: ON_WINDOWS });
}

console.log("Last DS Mile — installing via Claude Code\n");

const check = spawnSync("claude", ["--version"], { stdio: "ignore", shell: ON_WINDOWS });
if (check.error) {
  console.error("Claude Code CLI (`claude`) was not found on your PATH.");
  console.error("Install it first: https://claude.com/claude-code");
  console.error("\nThen re-run: npx github:stamkavid/last-ds-mile");
  process.exit(1);
}

console.log(`1/2  claude plugin marketplace add ${REPO}`);
const addMarketplace = run("claude", ["plugin", "marketplace", "add", REPO]);
if (addMarketplace.status !== 0) {
  console.error("\nFailed to add the marketplace — see the error above.");
  process.exit(addMarketplace.status ?? 1);
}

console.log(`\n2/2  claude plugin install ${PLUGIN}`);
const install = run("claude", ["plugin", "install", PLUGIN]);
if (install.status !== 0) {
  console.error("\nFailed to install the plugin — see the error above.");
  process.exit(install.status ?? 1);
}

console.log("\nDone. Last DS Mile is installed.");
console.log("Open Claude Code in a project and run /ds-frame to start the pipeline,");
console.log("or /ds at any point to see the map and get routed to the next stage.");
