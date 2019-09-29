
class IndentationError(Exception):

    def __init__(self, line):
        super().__init__(f"Indentation error at line {line}.")
