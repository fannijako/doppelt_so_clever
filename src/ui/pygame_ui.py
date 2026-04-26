import pygame

from src.board.board import Board
from src.logging_config import GameLogger

logger = GameLogger(__name__)


class PygameUI:
    def __init__(self, board: Board):
        self.board = board

        pygame.init()
        pygame.display.set_allow_screensaver(True)
        pygame.display.set_caption("Doppelt So Clever")

    def refresh(self) -> None:
        self._render()
        pygame.event.pump()

    def close(self) -> None:
        logger.info("PygameUI closed")
        pygame.quit()

    def _render(self) -> None:
        pass
