from src.game.game import Game
from src.ui.pygame_ui import PygameUI
from src.logging_config import GameLogger
from src.input_handler.pygame_input_handler import PygameInputHandler

logger = GameLogger(__name__)


class PygameGame(Game):  # pylint: disable=too-few-public-methods
    def __init__(self):
        super().__init__(input_handler=PygameInputHandler())
        self.ui = PygameUI(self.board)

    def play(self) -> int:
        try:
            return super().play()
        finally:
            self.ui.close()
