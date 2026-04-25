from src.input_handler.automatic_input_handler import AutomaticInputHandler


class AlwaysAcceptInputHandler(AutomaticInputHandler):
    def confirm(self, prompt: str) -> bool:
        return True
