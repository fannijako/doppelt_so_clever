from __future__ import annotations

import os
import glob
import time
import argparse
from dataclasses import dataclass

from tensorboard.backend.event_processing.event_accumulator import EventAccumulator


DEFAULT_LOG_DIR = "runs/doppelt_rl"
DEFAULT_INTERVAL_SECONDS = 600
DEFAULT_BATCH_SIZE = 64


@dataclass
class ScalarSnapshot:
    iter_estimate: int
    score_mean: float | None
    score_max: float | None
    eval_score: float | None
    entropy: float | None
    value_loss: float | None


def main() -> None:
    args = parse_arguments()
    if args.once:
        print_snapshot(read_latest_snapshot(args.log_dir, args.event_file, args.batch_size))
        return
    poll_loop(args.log_dir, args.event_file, args.batch_size, args.interval)


def poll_loop(log_dir: str, event_file: str | None, batch_size: int, interval: int) -> None:
    while True:
        print_snapshot(read_latest_snapshot(log_dir, event_file, batch_size))
        time.sleep(interval)


def read_latest_snapshot(
    log_dir: str, event_file: str | None, batch_size: int,
) -> ScalarSnapshot | None:
    path = event_file or find_latest_event_file(log_dir)
    if path is None:
        return None
    accumulator = EventAccumulator(path, size_guidance={"scalars": 0})
    accumulator.Reload()
    return build_snapshot(accumulator, batch_size)


def find_latest_event_file(log_dir: str) -> str | None:
    candidates = glob.glob(os.path.join(log_dir, "events.out.tfevents*"))
    if not candidates:
        return None
    return max(candidates, key=os.path.getmtime)


def build_snapshot(accumulator: EventAccumulator, batch_size: int) -> ScalarSnapshot:
    tags = accumulator.Tags()["scalars"]
    last_score_step = last_step(accumulator, "score/mean", tags) or 0
    return ScalarSnapshot(
        iter_estimate=last_score_step // max(batch_size, 1),
        score_mean=last_value(accumulator, "score/mean", tags),
        score_max=last_value(accumulator, "score/max", tags),
        eval_score=last_value(accumulator, "eval/mean_score", tags),
        entropy=last_value(accumulator, "loss/entropy", tags),
        value_loss=last_value(accumulator, "loss/value", tags),
    )


def last_value(accumulator: EventAccumulator, tag: str, tags: list[str]) -> float | None:
    if tag not in tags:
        return None
    events = accumulator.Scalars(tag)
    return events[-1].value if events else None


def last_step(accumulator: EventAccumulator, tag: str, tags: list[str]) -> int | None:
    if tag not in tags:
        return None
    events = accumulator.Scalars(tag)
    return events[-1].step if events else None


def print_snapshot(snapshot: ScalarSnapshot | None) -> None:
    timestamp = time.strftime("%H:%M:%S")
    if snapshot is None:
        print(f"[{timestamp}] (no data)", flush=True)
        return
    parts = [f"[{timestamp}] iter~{snapshot.iter_estimate}"]
    if snapshot.score_mean is not None:
        parts.append(f"score/mean={snapshot.score_mean:6.2f}")
    if snapshot.score_max is not None:
        parts.append(f"score/max={snapshot.score_max:5.1f}")
    if snapshot.eval_score is not None:
        parts.append(f"eval={snapshot.eval_score:6.2f}")
    if snapshot.entropy is not None:
        parts.append(f"entropy={snapshot.entropy:5.3f}")
    if snapshot.value_loss is not None:
        parts.append(f"value_loss={snapshot.value_loss:6.3f}")
    print("  ".join(parts), flush=True)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Monitor RL training progress from TensorBoard logs",
    )
    parser.add_argument("--log-dir", type=str, default=DEFAULT_LOG_DIR)
    parser.add_argument(
        "--event-file", type=str, default=None,
        help="Pin to specific event file (default: most recent)",
    )
    parser.add_argument(
        "--interval", type=int, default=DEFAULT_INTERVAL_SECONDS,
        help="Poll interval in seconds",
    )
    parser.add_argument(
        "--batch-size", type=int, default=DEFAULT_BATCH_SIZE,
        help="Episodes per iteration (used to estimate iter from step)",
    )
    parser.add_argument(
        "--once", action="store_true",
        help="Print a single snapshot and exit (no polling loop)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
