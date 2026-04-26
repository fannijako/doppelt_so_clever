from src.game.game import Game
from src.board.board import Board
from src.logging_config import GameLogger
from src.game.game_observer import GameObserver
from src.actions.action_handler import ActionHandler
from src.input_handler.base_input_handler import InputHandler

logger = GameLogger(__name__)


class PygameGame(Game):  # pylint: disable=too-few-public-methods
    def __init__(
        self,
        board: Board,
        input_handler: InputHandler,
        observer: GameObserver,
        action_handler: ActionHandler,
    ):
        super().__init__(
            input_handler=input_handler,
            board=board,
            observer=observer,
            action_handler=action_handler,
        )

    def play(self) -> int:
        try:
            return super().play()
        finally:
            self.observer.close()
