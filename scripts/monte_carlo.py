import os
import logging
import argparse
from typing import Callable
from datetime import datetime

import torch
import matplotlib.pyplot as plt

from src.game.game import Game
from src.board.board import Board
from src.logging_config import setup_logging
from src.game.score_rating import SCORE_CATEGORIES
from src.actions.action_handler import ActionHandler
from src.game.logging_observer import LoggingObserver
from src.input_handler.heuristics.always_accept import AlwaysAcceptInputHandler
from src.input_handler import (
    InputHandler,
    AutomaticInputHandler,
    ConsoleInputHandler,
    ModelInputHandler,
    RLInputHandler,
)
from src.game.rl_observer import RLObserver

from model.model import DoppeltSoCleverModel
from model.policy_network import PolicyNetwork
from scripts.train_rl import (
    require_phase3_metadata,
    checkpoint_strategic_features,
    assert_observer_state_size,
)


logger = logging.getLogger(__name__)

GameFactory = Callable[[], Game]


def main() -> None:
    arguments = parse_arguments()
    setup_logging(verbose=arguments.verbose, log_to_file=True, log_dir="logs")
    logger.info("args: %s", arguments)

    game_factory = get_game_factory(arguments)
    scores = run_simulation(arguments.rounds, game_factory)

    plot_scores(
        scores,
        f"monte_carlo_scores/{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.png"
    )


def run_simulation(rounds: int, game_factory: GameFactory) -> list[int]:
    scores = []
    for _ in range(rounds):
        game = game_factory()
        score = game.play()
        scores.append(score)

    logger.info("Scores: %s", scores)

    return scores


def get_game_factory(arguments: argparse.Namespace) -> GameFactory:
    if arguments.mode == "rl":
        return _create_rl_game_factory(arguments.checkpoint)
    input_handler = get_input_handler(arguments)
    return lambda: _create_standard_game(input_handler)


def _create_standard_game(input_handler: InputHandler) -> Game:
    board = Board()
    return Game(
        input_handler=input_handler,
        board=board,
        observer=LoggingObserver(),
        action_handler=ActionHandler(board=board),
    )


def plot_scores(scores: list[int], filename: str) -> None:
    os.makedirs("monte_carlo_scores", exist_ok=True)

    plt.figure()
    plt.hist(scores, bins=20)
    plt.xlabel("Score")
    plt.ylabel("Frequency")
    plt.title("Histogram of Scores")

    category_boundaries = sorted({lower for lower, _, _ in SCORE_CATEGORIES if lower > 0})
    for boundary in category_boundaries:
        plt.axvline(x=boundary, color='red', linestyle='--', alpha=0.7)

    max_score = 350
    plt.xlim(0, max_score)

    ymax = plt.ylim()[1]
    for lower, upper, label in SCORE_CATEGORIES:
        end = upper if upper is not None else max_score
        mid = (lower + end) / 2
        plt.text(mid, ymax * 0.95, label, ha='center', va='top', rotation=90, fontsize=8, color='red')

    plt.savefig(filename)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("-r", "--rounds", type=int, default=1000, help="Number of rounds to play")
    parser.add_argument(
        "--mode",
        choices=["console", "automatic", "always-accept", "model", "rl"],
        default="automatic",
        help="Input mode: automatic (default), console, always-accept, model, or rl"
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        default=None,
        help="Path to RL model checkpoint (for rl mode)"
    )
    return parser.parse_args()


def get_input_handler(arguments: argparse.Namespace) -> InputHandler:
    handlers = {
        "console": ConsoleInputHandler,
        "always-accept": AlwaysAcceptInputHandler,
        "model": lambda: ModelInputHandler(DoppeltSoCleverModel()),
        "automatic": AutomaticInputHandler,
    }

    handler_factory = handlers.get(arguments.mode)
    if handler_factory is None:
        raise ValueError(f"Unknown mode: {arguments.mode}")
    return handler_factory()


def _create_rl_game_factory(checkpoint_path: str | None) -> GameFactory:
    if checkpoint_path is None:
        checkpoint_path = _find_latest_checkpoint()
    policy, augmented, strategic_features = _load_policy(checkpoint_path)
    policy_fn = _create_policy_fn(policy)

    def factory() -> Game:
        board = Board()
        observer = RLObserver(board, augmented=augmented, strategic_features=strategic_features)
        assert_observer_state_size(observer, policy.trunk[0].in_features, source=checkpoint_path)
        handler = RLInputHandler(observer, policy_fn, training=False)
        return Game(
            input_handler=handler,
            board=board,
            observer=observer,
            action_handler=ActionHandler(board=board),
        )

    return factory


def _load_policy(checkpoint_path: str) -> tuple[PolicyNetwork, bool, bool]:
    logger.info("Loading RL model from checkpoint: %s", checkpoint_path)
    checkpoint = torch.load(checkpoint_path, weights_only=True)
    require_phase3_metadata(checkpoint, checkpoint_path)
    policy = PolicyNetwork(
        state_size=checkpoint["state_size"],
        hidden1=checkpoint.get("hidden1", 256),
        hidden2=checkpoint.get("hidden2", 128),
    )
    policy.load_state_dict(checkpoint["policy_state_dict"])
    policy.eval()
    return policy, checkpoint["augmented"], checkpoint_strategic_features(checkpoint)


def _create_policy_fn(policy: PolicyNetwork):
    @torch.no_grad()
    def policy_fn(state: list[float], action_mask: list[bool]) -> tuple[int, float, float]:
        state_t = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
        mask_t = torch.tensor([float(m) for m in action_mask], dtype=torch.float32).unsqueeze(0)
        logits, value = policy(state_t)
        masked_logits = logits + (1.0 - mask_t) * (-1e8)
        action = masked_logits.argmax(dim=-1)
        dist = torch.distributions.Categorical(logits=masked_logits)
        log_prob = dist.log_prob(action)
        return action.item(), log_prob.item(), value.item()

    return policy_fn


def _find_latest_checkpoint() -> str:
    checkpoint_dir = "model/checkpoints"
    if not os.path.exists(checkpoint_dir):
        raise ValueError(f"Checkpoint directory {checkpoint_dir} does not exist")

    checkpoints = [f for f in os.listdir(checkpoint_dir) if f.endswith(".pt")]
    if not checkpoints:
        raise ValueError(f"No checkpoints found in {checkpoint_dir}")

    latest = max(checkpoints)
    return os.path.join(checkpoint_dir, latest)


if __name__ == "__main__":
    main()
