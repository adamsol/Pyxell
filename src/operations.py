
__all__ = [
    'UnaryOperation', 'BinaryOperation', 'TernaryOperation',
]


class Operation:

    def __init__(self, type):
        self.type = type


class UnaryOperation(Operation):

    def __init__(self, op, value, **kwargs):
        super().__init__(**kwargs)
        self.op = op
        self.value = value

    def __str__(self):
        return f'({self.op}{self.value})'


class BinaryOperation(Operation):

    def __init__(self, value1, op, value2, **kwargs):
        super().__init__(**kwargs)
        self.value1 = value1
        self.op = op
        self.value2 = value2

    def __str__(self):
        return f'({self.value1} {self.op} {self.value2})'


class TernaryOperation(Operation):

    def __init__(self, value1, op1, value2, op2, value3, **kwargs):
        super().__init__(**kwargs)
        self.value1 = value1
        self.op1 = op1
        self.value2 = value2
        self.op2 = op2
        self.value3 = value3

    def __str__(self):
        return f'({self.value1} {self.op1} {self.value2} {self.op2} {self.value3})'

