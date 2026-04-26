from src.game.game import Game
from src.board.board import Board
from src.ui.pygame_ui import PygameUI
from src.logging_config import GameLogger
from src.input_handler.pygame_input_handler import PygameInputHandler

logger = GameLogger(__name__)


class PygameGame(Game):  # pylint: disable=too-few-public-methods
    def __init__(self):
        board = Board()
        self.ui = PygameUI(board)
        super().__init__(
            input_handler=PygameInputHandler(),
            board=board,
            observer=self.ui,
        )

    def play(self) -> int:
        try:
            return super().play()
        finally:
            self.ui.close()
