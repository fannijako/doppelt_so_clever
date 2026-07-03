#!/bin/bash
set -euxo pipefail

dnf install -y python3.11

mkdir -p /opt/train
cd /opt/train
aws s3 cp "s3://__BUCKET__/code/__RUN_ID__.tar.gz" code.tar.gz
tar xzf code.tar.gz
python3.11 -m venv .venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -e '.[rl]'

if [ "__RESUME__" = "1" ]; then
  mkdir -p model/checkpoints
  aws s3 cp "s3://__BUCKET__/code/__RUN_ID__-resume.pt" model/checkpoints/resume.pt
fi

cat > /opt/train/run.sh <<'RUNEOF'
#!/bin/bash
set -u
cd /opt/train
source .venv/bin/activate
(
  while true; do
    sleep 300
    aws s3 sync model/checkpoints "s3://__BUCKET__/results/__RUN_ID__/checkpoints" || true
    aws s3 sync runs "s3://__BUCKET__/results/__RUN_ID__/runs" || true
  done
) &
SYNC_PID=$!
python main.py train --num-workers "$(nproc)" __TRAIN_ARGS__
EXIT_CODE=$?
kill "$SYNC_PID" 2>/dev/null || true
aws s3 sync model/checkpoints "s3://__BUCKET__/results/__RUN_ID__/checkpoints" || true
aws s3 sync runs "s3://__BUCKET__/results/__RUN_ID__/runs" || true
echo "$EXIT_CODE" | aws s3 cp - "s3://__BUCKET__/results/__RUN_ID__/status.txt"
if [ "__AUTO_TERMINATE__" = "1" ]; then
  shutdown -h now
fi
RUNEOF

chmod +x /opt/train/run.sh
nohup /opt/train/run.sh > /var/log/rl-training.log 2>&1 &
