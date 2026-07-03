# EC2 Training — Design

**Goal:** run `python main.py train` on an EC2 instance; results land back locally. One-command launch once the AWS account exists (account setup is manual, out of scope).

## Approach

Bash launcher + user-data via AWS CLI. Rejected: CDK stack (needs Node + `cdk bootstrap` in a fresh account — heavy for one instance), Docker-on-EC2 (image build on-instance, no registry — extra moving parts, same result).

## Components (`scripts/aws/`)

| File | Purpose |
|------|---------|
| `setup_aws.sh` | One-time, idempotent: S3 bucket `doppelt-rl-<account-id>`, IAM role + instance profile (`AmazonSSMManagedInstanceCore` + S3 scoped to the bucket) |
| `launch_training.sh` | `git archive HEAD` → S3, render `user_data.sh.tpl`, `aws ec2 run-instances` |
| `user_data.sh.tpl` | AL2023 bootstrap: python3.11 venv, `pip install -e .[rl]`, run training via nohup, S3 sync loop every 5 min, final sync + status file + optional shutdown |
| `fetch_results.sh` | Sync `s3://…/results/<run-id>/` → `model/checkpoints_ec2/<run-id>/` + `runs_ec2/<run-id>/`, print status |

## Decisions

- **Code transfer:** git archive → S3. No GitHub token on the instance; works if repo goes private. Uncommitted changes are NOT shipped (documented).
- **Access:** SSM Session Manager only. No key pair, no port 22, default VPC/SG.
- **Instance:** default `c7g.4xlarge` (16 vCPU Graviton; training is CPU-bound pure-Python sim, torch ships aarch64 wheels). `INSTANCE_TYPE`, `SPOT=1`, `AUTO_TERMINATE=0`, `TRAIN_ARGS`, `RESUME_CHECKPOINT` env-overridable. AMI resolved at launch from the AL2023 SSM parameter matching the instance arch. Root volume 20 GiB gp3 (torch + venv exceed the 8 GiB default).
- **Training invocation:** `python main.py train --num-workers $(nproc) $TRAIN_ARGS` (mirrors Dockerfile).
- **Spot resume:** `RESUME_CHECKPOINT=<local .pt>` uploads the checkpoint and appends `--resume`.
- **Monitoring:** `fetch_results.sh` then existing `make monitor-rl MONITOR_ARGS="--log-dir runs_ec2/<run-id> --once"`; live logs via `aws ssm start-session` → `tail -f /var/log/rl-training.log`.
- **Cost (us-east-1, approx):** c7g.4xlarge ~$0.58/h on-demand, ~$0.20–0.25/h spot. Auto-terminate on completion is the default.

## Error handling

- `set -euo pipefail` everywhere; launch fails fast if setup resources are missing.
- Training exit code written to `s3://…/results/<run-id>/status.txt` before shutdown.
- Sync loop is best-effort (`|| true`) so a transient S3 error doesn't kill training.

## Verification (no account yet — no e2e)

`bash -n` all scripts, shellcheck if available, render the user-data template with dummy values and `bash -n` the result.
