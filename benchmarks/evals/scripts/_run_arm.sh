#!/usr/bin/env bash
# Executes one (eval, arm, trial) workspace via claude -p, with the plugin
# under test toggled and every ancillary plugin disabled in both arms.
# Usage: _run_arm.sh <eval-N> <with_skill|without_skill> <trial-N>
set -euo pipefail

EVAL="$1"
ARM="$2"
TRIAL="$3"
ROOT="C:/Users/Stamatis/Downloads/last-ds-mile/benchmarks/evals/credit-card-fraud/results/iteration-2"
WS="$ROOT/$EVAL/$ARM/$TRIAL"

if [ "$ARM" = "with_skill" ]; then
  LDM=true
else
  LDM=false
fi

SETTINGS="{\"enabledPlugins\":{\"last-ds-mile@last-ds-mile\":$LDM,\"context7@claude-plugins-official\":false,\"mgrep@Mixedbread-Grep\":false,\"superpowers@claude-plugins-official\":false,\"playwright@claude-plugins-official\":false,\"agent-skills@local-desktop-app-uploads\":false,\"agent-skills@addy-agent-skills\":false}}"

cd "$WS/outputs"
PROMPT="$(cat ../prompt.md)"

claude -p "$PROMPT" \
  --model claude-sonnet-5 \
  --settings "$SETTINGS" \
  --allowedTools "Read Write Edit Bash Glob Grep" \
  --permission-mode default \
  --max-budget-usd 3 \
  --output-format stream-json --verbose \
  > ../transcript.jsonl 2> ../stderr.log
CODE=$?
echo "$CODE" > ../exit_code.txt
echo "DONE $EVAL $ARM $TRIAL exit=$CODE"
