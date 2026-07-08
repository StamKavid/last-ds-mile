#!/usr/bin/env bash
# Find a working Python 3 interpreter and exec the hook with it.
#
# On Windows + Git Bash, `python3` typically resolves to the Microsoft Store stub
# at C:\Users\<user>\AppData\Local\Microsoft\WindowsApps\python3, which exits
# non-zero silently in non-TTY subprocess context. This shim probes each
# candidate and skips any that fails, so the Store stub falls through to the
# real python.org install (`python` in Git Bash) or the `py -3` launcher.
#
# Usage: bash "${CLAUDE_PLUGIN_ROOT}/hooks/ds-python.sh" "${CLAUDE_PLUGIN_ROOT}/hooks/<script>.py"
set -e

# Git Bash hands script paths to this shim in POSIX form (/c/Users/...). When we
# exec a Windows python.exe, it interprets a leading `/` as the current drive's
# root and fails with ENOENT. Convert absolute path args to native Windows form
# via `cygpath -w` (a Git Bash builtin, absent on macOS/Linux where this is a
# no-op since the `command -v` guard skips it).
if command -v cygpath >/dev/null 2>&1; then
    converted=()
    for a in "$@"; do
        case "$a" in
            /*) converted+=("$(cygpath -w "$a")") ;;
            *)  converted+=("$a") ;;
        esac
    done
    set -- "${converted[@]}"
fi

probe() {
    # Exits 0 only for a real Python 3 interpreter (not Python 2, not a
    # non-functional stub).
    "$@" -c "import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)" 2>/dev/null
}

for cmd in "python3" "python" "py -3"; do
    # shellcheck disable=SC2086
    if probe $cmd; then
        # shellcheck disable=SC2086
        exec $cmd "$@"
    fi
done

echo "last-ds-mile: no working Python 3 interpreter found (tried python3, python, py -3)." >&2
echo "  install Python 3 from https://python.org" >&2
exit 1
