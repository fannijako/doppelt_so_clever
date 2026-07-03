# Training on EC2

Runs `python main.py train` on a throwaway EC2 instance; checkpoints and TensorBoard logs sync to S3 every 5 min and the instance terminates itself when training ends.

## Prerequisites

- AWS CLI v2 with credentials and a default region (`aws configure`)
- Session Manager plugin for live logs (`brew install --cask session-manager-plugin`) — optional

## One-time setup

```bash
scripts/aws/setup_aws.sh
```

Creates (idempotent): S3 bucket `doppelt-rl-<account-id>`, IAM role + instance profile `doppelt-rl-ec2` (SSM access + S3 scoped to that bucket). No key pair, no security group — instance access is SSM-only.

## Launch

```bash
scripts/aws/launch_training.sh
```

Ships `git archive HEAD` (uncommitted changes are NOT included) to S3, boots Amazon Linux 2023, installs python3.11 + `.[rl]`, runs `python main.py train --num-workers $(nproc) $TRAIN_ARGS`.

Overrides (env vars):

| Var | Default | Notes |
|-----|---------|-------|
| `TRAIN_ARGS` | `--iterations 5000` | appended to the train command |
| `INSTANCE_TYPE` | `c7g.4xlarge` | 16 vCPU Graviton; AMI arch auto-resolved |
| `SPOT` | `0` | `1` = one-time spot request |
| `AUTO_TERMINATE` | `1` | `0` keeps the instance up after training |
| `RESUME_CHECKPOINT` | — | local `.pt` path; uploaded and passed via `--resume` |

```bash
TRAIN_ARGS="--iterations 10000 --reward-mode min-section --num-workers 16" SPOT=1 scripts/aws/launch_training.sh
```

Note: `--num-workers` in `TRAIN_ARGS` overrides the `$(nproc)` default because argparse takes the last occurrence.

## Monitor

```bash
scripts/aws/fetch_results.sh            # sync latest run down (or pass a run id)
make monitor-rl MONITOR_ARGS="--log-dir runs_ec2/<run-id> --once"

aws ssm start-session --target <instance-id>   # live: tail -f /var/log/rl-training.log
```

`status.txt` in the run's S3 prefix holds the training exit code; `fetch_results.sh` prints it ("still running" until final sync).

## Cost (us-east-1, approximate)

| | c7g.4xlarge |
|---|---|
| on-demand | ~$0.58/h |
| spot | ~$0.20–0.25/h |

Plus ~cents for the 20 GiB gp3 root volume and S3. Auto-terminate is on by default; a spot interruption loses at most 5 min of sync — relaunch with `RESUME_CHECKPOINT=model/checkpoints_ec2/<run-id>/<checkpoint>.pt`.

## Smoke test (no AWS account needed)

```bash
pip install 'moto[server]'
scripts/aws/moto_smoke.sh
```

Runs setup (twice, for idempotency), launch (on-demand / spot / resume), and fetch against a local moto mock; asserts rendered user-data, S3 objects, and instance state. Starts its own moto server if none is listening.

## Teardown

Everything except the S3 bucket is free when idle. To remove:

```bash
aws s3 rb "s3://doppelt-rl-$(aws sts get-caller-identity --query Account --output text)" --force
aws iam remove-role-from-instance-profile --instance-profile-name doppelt-rl-ec2 --role-name doppelt-rl-ec2
aws iam delete-instance-profile --instance-profile-name doppelt-rl-ec2
aws iam detach-role-policy --role-name doppelt-rl-ec2 --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
aws iam delete-role-policy --role-name doppelt-rl-ec2 --policy-name s3-results
aws iam delete-role --role-name doppelt-rl-ec2
```
