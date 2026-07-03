#!/usr/bin/env bash
set -uo pipefail
cd "$(git rev-parse --show-toplevel)" || exit 1

export AWS_ENDPOINT_URL=${AWS_ENDPOINT_URL:-http://127.0.0.1:4599}
export AWS_ACCESS_KEY_ID=testing
export AWS_SECRET_ACCESS_KEY=testing
export AWS_REGION=us-east-1
export AWS_PAGER=""

MOTO_PID=""
if ! curl -s "$AWS_ENDPOINT_URL/moto-api/" >/dev/null 2>&1; then
  MOTO_IAM_LOAD_MANAGED_POLICIES=true python3 -m moto.server -p "${AWS_ENDPOINT_URL##*:}" >/dev/null 2>&1 &
  MOTO_PID=$!
  trap '[ -n "$MOTO_PID" ] && kill "$MOTO_PID" 2>/dev/null' EXIT
  for _ in $(seq 1 20); do curl -s "$AWS_ENDPOINT_URL/moto-api/" >/dev/null 2>&1 && break; sleep 0.5; done
  curl -s "$AWS_ENDPOINT_URL/moto-api/" >/dev/null 2>&1 \
    || { echo "moto server not reachable — pip install 'moto[server]' first" >&2; exit 1; }
fi

PASS=0
FAIL=0
check() {
  if eval "$2" >/dev/null 2>&1; then
    echo "PASS: $1"; PASS=$((PASS+1))
  else
    echo "FAIL: $1"; FAIL=$((FAIL+1))
  fi
}

echo "== setup_aws.sh =="
OUT1=$(bash scripts/aws/setup_aws.sh 2>&1); RC1=$?
check "setup exits 0" "[ $RC1 -eq 0 ]"
check "setup prints ready line" "echo \"\$OUT1\" | grep -q '^ready:'"
OUT2=$(bash scripts/aws/setup_aws.sh 2>&1); RC2=$?
check "setup rerun idempotent" "[ $RC2 -eq 0 ]"

ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
BUCKET=doppelt-rl-$ACCOUNT
check "bucket exists" "aws s3api head-bucket --bucket $BUCKET"
check "instance profile has role" "[ \"\$(aws iam get-instance-profile --instance-profile-name doppelt-rl-ec2 --query 'InstanceProfile.Roles[0].RoleName' --output text)\" = doppelt-rl-ec2 ]"
check "ssm managed policy attached" "aws iam list-attached-role-policies --role-name doppelt-rl-ec2 --output text | grep -q AmazonSSMManagedInstanceCore"
check "s3 inline policy present" "aws iam get-role-policy --role-name doppelt-rl-ec2 --policy-name s3-results"

AMI=$(aws ec2 describe-images --query 'Images[0].ImageId' --output text)
for arch in arm64 x86_64; do
  P=/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-$arch
  aws ssm get-parameter --name "$P" >/dev/null 2>&1 \
    || aws ssm put-parameter --name "$P" --type String --value "$AMI" >/dev/null
done

echo "== launch_training.sh (on-demand) =="
OUT4=$(TRAIN_ARGS="--iterations 50" bash scripts/aws/launch_training.sh 2>&1); RC4=$?
check "launch exits 0" "[ $RC4 -eq 0 ]"
RUN_ID=$(echo "$OUT4" | awk '/^run_id:/{print $2}')
INSTANCE_ID=$(echo "$OUT4" | awk '/^instance:/{print $2}')
check "code tarball in s3" "aws s3 ls s3://$BUCKET/code/$RUN_ID.tar.gz"
check "instance is running" "[ \"\$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query 'Reservations[0].Instances[0].State.Name' --output text)\" = running ]"
UD=$(aws ec2 describe-instance-attribute --instance-id "$INSTANCE_ID" --attribute userData --query 'UserData.Value' --output text | base64 -d)
check "user-data has train command" "echo \"\$UD\" | grep -q -- '--iterations 50'"
check "user-data no placeholders" "! echo \"\$UD\" | grep -q __"

echo "== fetch_results.sh =="
echo fake-weights | aws s3 cp - "s3://$BUCKET/results/$RUN_ID/checkpoints/best.pt" >/dev/null
echo fake-events | aws s3 cp - "s3://$BUCKET/results/$RUN_ID/runs/doppelt_rl/events.out.tfevents.1" >/dev/null
echo 0 | aws s3 cp - "s3://$BUCKET/results/$RUN_ID/status.txt" >/dev/null
OUT5=$(bash scripts/aws/fetch_results.sh 2>&1); RC5=$?
check "fetch exits 0" "[ $RC5 -eq 0 ]"
check "checkpoint synced" "[ -f model/checkpoints_ec2/$RUN_ID/best.pt ]"
check "status printed" "echo \"\$OUT5\" | grep -q 'exit code: 0'"

echo "== launch variants =="
OUT6=$(TRAIN_ARGS="--iterations 5" SPOT=1 bash scripts/aws/launch_training.sh 2>&1); RC6=$?
check "spot launch exits 0" "[ $RC6 -eq 0 ]"
sleep 1
DUMMY=$(mktemp); echo fake-ckpt > "$DUMMY"
OUT7=$(TRAIN_ARGS="--iterations 5" RESUME_CHECKPOINT="$DUMMY" bash scripts/aws/launch_training.sh 2>&1); RC7=$?
rm -f "$DUMMY"
check "resume launch exits 0" "[ $RC7 -eq 0 ]"
RUN_ID7=$(echo "$OUT7" | awk '/^run_id:/{print $2}')
INSTANCE_ID7=$(echo "$OUT7" | awk '/^instance:/{print $2}')
check "resume ckpt in s3" "aws s3 ls s3://$BUCKET/code/$RUN_ID7-resume.pt"
UD7=$(aws ec2 describe-instance-attribute --instance-id "$INSTANCE_ID7" --attribute userData --query 'UserData.Value' --output text | base64 -d)
check "train args have --resume" "echo \"\$UD7\" | grep -q -- '--resume model/checkpoints/resume.pt'"

rm -rf "model/checkpoints_ec2/$RUN_ID" "runs_ec2/$RUN_ID"
rmdir model/checkpoints_ec2 runs_ec2 2>/dev/null

echo ""
echo "RESULT: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
