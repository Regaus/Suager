class RegausError(Exception):
    def __init__(self, text: str = "None"):
        super().__init__(text)


class AqosError(RegausError):
    def __init__(self, text: str = "None"):
        super().__init__(text=text)
