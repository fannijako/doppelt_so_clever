class DoppeltSoCleverModel:  # pylint: disable=too-few-public-methods
    def predict(self, state):
        if state == ["y", "n"]:
            return self.predict_confirm()
        if 0 in state:
            return self.predict_index()
        return self.predict_color(state)

    def predict_confirm(self):
        return "y"

    def predict_index(self):
        return 0

    def predict_color(self, state):
        if 'yellow' in state:
            return 'yellow'
        if 'white' in state:
            return 'white'
        if 'pink' in state:
            return 'pink'
        if 'blue' in state:
            return 'blue'
        if 'grey' in state:
            return 'grey'
        return 'green'
