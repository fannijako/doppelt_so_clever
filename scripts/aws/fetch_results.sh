#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET=doppelt-rl-${ACCOUNT_ID}
RUN_ID=${1:-$(aws s3 ls "s3://$BUCKET/results/" 2>/dev/null | awk '{print $2}' | tr -d / | sort | tail -1 || true)}
[ -n "$RUN_ID" ] || { echo "no runs found in s3://$BUCKET/results/" >&2; exit 1; }

aws s3 sync "s3://$BUCKET/results/$RUN_ID/checkpoints" "model/checkpoints_ec2/$RUN_ID"
aws s3 sync "s3://$BUCKET/results/$RUN_ID/runs" "runs_ec2/$RUN_ID"

STATUS=$(aws s3 cp "s3://$BUCKET/results/$RUN_ID/status.txt" - 2>/dev/null || echo "still running")
echo "run $RUN_ID exit code: $STATUS (0 = success)"
echo "checkpoints: model/checkpoints_ec2/$RUN_ID/"
echo "monitor:     make monitor-rl MONITOR_ARGS=\"--log-dir runs_ec2/$RUN_ID --once\""
