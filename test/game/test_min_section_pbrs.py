import random

import pytest

from src.actions.action_handler import ActionHandler
from src.board.board import Board
from src.game.game import Game
from src.game.reward_shaper import MIN_SECTION_PBRS_REWARD_CONFIG
from src.game.rl_observer import RLObserver
from src.input_handler.model.rl_input_handler import RLInputHandler


def _random_policy(_state, action_mask):
    legal = [i for i, m in enumerate(action_mask) if m]
    return random.choice(legal), -0.5, 0.0


def _play_full_episode(seed: int) -> tuple[RLInputHandler, Board]:
    random.seed(seed)
    board = Board()
    observer = RLObserver(board, augmented=False)
    handler = RLInputHandler(
        observer, _random_policy, training=True,
        reward_config=MIN_SECTION_PBRS_REWARD_CONFIG,
    )
    game = Game(
        input_handler=handler,
        board=board,
        observer=observer,
        action_handler=ActionHandler(board=board),
    )
    game.play()
    handler.flush_terminal_step_reward()
    return handler, board


@pytest.mark.parametrize("seed", [0, 1, 2, 3])
def test_step_rewards_telescope_to_final_potential(seed):
    handler, board = _play_full_episode(seed)
    total_shaping = sum(t.reward for t in handler.trajectory)
    assert total_shaping == pytest.approx(0.1 * board.min_section_score())
