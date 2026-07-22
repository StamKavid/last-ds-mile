# Security Policy

## Scope

Last DS Mile is a Claude Code plugin: Markdown skills/commands plus four small,
stdlib-only Python hooks (`hooks/`) that run locally inside your Claude Code session.
It makes no network calls and ships no server or service. See [AUDIT.md](AUDIT.md) for
a complete, verifiable account of what each hook reads, writes, and does — that file
is the authoritative security reference for this plugin, not a summary of it.

Security issues in scope include (non-exhaustive):

- A hook reading, writing, or transmitting more than `AUDIT.md` claims
- A way for plugin content (skills, commands, lesson files) to cause an agent to
  execute untrusted code or exfiltrate data from a user's project
- A bypass of the `scan_untrusted_input.py` checks (e.g., a pickle/joblib load or a
  hidden-unicode payload that should be flagged but isn't)
- Supply-chain issues in the `npx stamkavid/last-ds-mile` installer (`bin/install.mjs`)

Out of scope: vulnerabilities in Claude Code itself, or in datasets/notebooks a user
brings into their own project — report those upstream or handle per your own project's
policy.

## Reporting a vulnerability

Please do not open a public GitHub issue for a security concern.

Instead, report privately via **GitHub Security Advisories**:
https://github.com/stamkavid/last-ds-mile/security/advisories/new

If that's not accessible, email **stamkavid@gmail.com** with a description of the
issue, the affected file(s), and reproduction steps. You'll get an acknowledgment
within a few days; fixes are released as a patch version with the issue credited in
[CHANGELOG.md](CHANGELOG.md) unless you ask to stay anonymous.

## Supported versions

This project is pre-1.0 and moves fast; only the latest published release is
supported. Update to the newest version before reporting to confirm the issue still
reproduces.
