#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

INSTANCE_TYPE=${INSTANCE_TYPE:-c7g.4xlarge}
SPOT=${SPOT:-0}
AUTO_TERMINATE=${AUTO_TERMINATE:-1}
TRAIN_ARGS=${TRAIN_ARGS:---iterations 5000}
RESUME_CHECKPOINT=${RESUME_CHECKPOINT:-}
ROLE_NAME=doppelt-rl-ec2
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET=doppelt-rl-${ACCOUNT_ID}
RUN_ID=$(date +%Y%m%d-%H%M%S)

aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null \
  || { echo "bucket $BUCKET missing — run scripts/aws/setup_aws.sh first" >&2; exit 1; }

if ! git diff --quiet HEAD; then
  echo "warning: uncommitted changes are NOT included (code ships via git archive HEAD)" >&2
fi

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

git archive --format=tar.gz -o "$TMP/code.tar.gz" HEAD
aws s3 cp "$TMP/code.tar.gz" "s3://$BUCKET/code/${RUN_ID}.tar.gz"

RESUME_FLAG=0
if [ -n "$RESUME_CHECKPOINT" ]; then
  aws s3 cp "$RESUME_CHECKPOINT" "s3://$BUCKET/code/${RUN_ID}-resume.pt"
  TRAIN_ARGS="$TRAIN_ARGS --resume model/checkpoints/resume.pt"
  RESUME_FLAG=1
fi

ARCH=$(aws ec2 describe-instance-types --instance-types "$INSTANCE_TYPE" \
  --query 'InstanceTypes[0].ProcessorInfo.SupportedArchitectures[0]' --output text)
AMI_ID=$(aws ssm get-parameter \
  --name "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-${ARCH}" \
  --query Parameter.Value --output text)

sed -e "s|__BUCKET__|$BUCKET|g" \
    -e "s|__RUN_ID__|$RUN_ID|g" \
    -e "s|__TRAIN_ARGS__|$TRAIN_ARGS|g" \
    -e "s|__AUTO_TERMINATE__|$AUTO_TERMINATE|g" \
    -e "s|__RESUME__|$RESUME_FLAG|g" \
    scripts/aws/user_data.sh.tpl > "$TMP/user_data.sh"
bash -n "$TMP/user_data.sh"

EXTRA_OPTS=()
if [ "$SPOT" = "1" ]; then
  EXTRA_OPTS=(--instance-market-options 'MarketType=spot,SpotOptions={SpotInstanceType=one-time}')
else
  EXTRA_OPTS=(--instance-initiated-shutdown-behavior terminate)
fi

INSTANCE_ID=""
for attempt in 1 2 3 4 5; do
  if INSTANCE_ID=$(aws ec2 run-instances \
      --image-id "$AMI_ID" \
      --instance-type "$INSTANCE_TYPE" \
      --iam-instance-profile "Name=$ROLE_NAME" \
      --user-data "file://$TMP/user_data.sh" \
      --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":20,"VolumeType":"gp3"}}]' \
      --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=doppelt-rl-${RUN_ID}}]" \
      ${EXTRA_OPTS[@]+"${EXTRA_OPTS[@]}"} \
      --query 'Instances[0].InstanceId' --output text); then
    break
  fi
  echo "run-instances failed (attempt $attempt/5, instance profile may still be propagating) — retrying in 10s" >&2
  sleep 10
done
[ -n "$INSTANCE_ID" ] || { echo "run-instances failed after 5 attempts" >&2; exit 1; }

echo "run_id:      $RUN_ID"
echo "instance:    $INSTANCE_ID ($INSTANCE_TYPE, spot=$SPOT)"
echo "train_args:  --num-workers \$(nproc) $TRAIN_ARGS"
echo "results:     s3://$BUCKET/results/$RUN_ID/"
echo "logs:        aws ssm start-session --target $INSTANCE_ID   # then: tail -f /var/log/rl-training.log"
echo "fetch:       scripts/aws/fetch_results.sh $RUN_ID"
