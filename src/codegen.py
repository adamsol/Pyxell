
import re

INDENT = '\t'


class Collection:
    def __init__(self, *content):
        self.content = list(content)

    def append(self, elem):
        self.content.append(elem)

    def __str__(self):
        return '\n'.join(map(str, self.content)) + '\n'


class Block(Collection):
    def __str__(self):
        return '{\n' + '\n'.join(re.sub('^', INDENT, str(elem), flags=re.MULTILINE) for elem in self.content) + '\n}'


class Wrapper:
    def __init__(self, formatter, *parts):
        self.formatter = formatter
        self.parts = parts

    def __str__(self):
        return self.formatter.format(*self.parts)


class Statement(Wrapper):
    def __init__(self, *parts):
        super().__init__(' '.join(['{}']*len(parts))+';', *parts)


class Var(Wrapper):
    def __init__(self, var, value=None):
        super().__init__('{} {}' + (' = {}' if value else ''), var.type, var.name, value)


class Const(Wrapper):
    def __init__(self, var, value):
        super().__init__('const {} {} = {}', var.type, var.name, value)


class Label(Wrapper):
    def __init__(self, name):
        super().__init__('{}:', name)


class If(Wrapper):
    def __init__(self, cond, if_block, else_block=None):
        super().__init__('if ({}) {}' + (' else {}' if else_block and else_block.content else ''), cond, if_block, else_block)


class While(Wrapper):
    def __init__(self, cond, body):
        super().__init__('while ({}) {}', cond, body)


class For(Wrapper):
    def __init__(self, init, cond, update, body):
        super().__init__('for ({}; {}; {}) {}', init, cond, update, body)


class Function(Wrapper):
    def __init__(self, ret, name, args, body):
        super().__init__('{}{}({}) {}', f'{ret} '.lstrip(), name, ', '.join(str(Var(arg)) for arg in args), body)


class Struct(Wrapper):
    def __init__(self, name, body, base=None):
        if base is None:
            super().__init__('struct {} {};', name, body)
        else:
            super().__init__('struct {}: {} {};', name, base, body)
