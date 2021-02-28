
# Recursive-descent parser with Pratt-style expression parsing. Based on:
# http://www.craftinginterpreters.com/parsing-expressions.html
# http://journal.stuffwithstuff.com/2011/03/19/pratt-parsers-expression-parsing-made-easy/

import json
import re
from collections import defaultdict
from contextlib import contextmanager

from .errors import PyxellError as err
from .lexer import tokenize, Token, ASSIGNMENT_OPERATORS


class Fixity:
    PREFIX = True
    NON_PREFIX = False


EXPR_OPERATOR_PRECEDENCE = defaultdict(lambda: 0)

for precedence, (fixity, ops) in enumerate(reversed([
    (Fixity.NON_PREFIX, ['.', '?.']),
    (Fixity.NON_PREFIX, ['[', '?[']),
    (Fixity.NON_PREFIX, ['(', '@(']),
    (Fixity.NON_PREFIX, ['!']),
    (Fixity.NON_PREFIX, ['^', '^^']),
    (Fixity.PREFIX, ['+', '-']),
    (Fixity.NON_PREFIX, ['/']),
    (Fixity.NON_PREFIX, ['//', '%', '*', '&']),
    (Fixity.NON_PREFIX, ['+', '-']),
    (Fixity.NON_PREFIX, ['%%']),
    (Fixity.NON_PREFIX, ['??']),
    (Fixity.NON_PREFIX, ['...', '..']),
    (Fixity.NON_PREFIX, ['by']),
    (Fixity.PREFIX, ['...']),
    (Fixity.NON_PREFIX, ['==', '!=', '<', '<=', '>', '>=']),
    (Fixity.NON_PREFIX, ['in', 'not']),
    (Fixity.NON_PREFIX, ['is']),
    (Fixity.PREFIX, ['not']),
    (Fixity.NON_PREFIX, ['and']),
    (Fixity.NON_PREFIX, ['or']),
    (Fixity.NON_PREFIX, ['?']),
    (Fixity.PREFIX, ['lambda']),
]), 1):
    for op in ops:
        EXPR_OPERATOR_PRECEDENCE[fixity, op] = precedence


TYPE_OPERATOR_PRECEDENCE = defaultdict(lambda: 0)

for precedence, op in enumerate(reversed(['?', '*', '->']), 1):
    TYPE_OPERATOR_PRECEDENCE[op] = precedence


class PyxellParser:
    def __init__(self, lines, filepath, start_position=(1, 1)):
        tokens = tokenize(lines, start_position)
        self.tokens = tokens[:-1]
        self.eof_token = tokens[-1]
        self.index = 0
        self.filepath = filepath

    def raise_syntax_error(self, token):
        raise err(self.filepath, token.position, err.InvalidSyntax())

    def eof(self):
        return self.index >= len(self.tokens)

    def peek(self, offset=0):
        if self.index + offset < len(self.tokens):
            return self.tokens[self.index + offset]
        return self.eof_token

    def pop(self):
        token = self.peek()
        self.index += 1
        return token

    def backtrack(self, count=1):
        self.index -= count

    def check(self, *words):
        """ Returns whether the current tokens match all the given words. """
        for i, word in enumerate(words):
            if self.peek(i).text != word:
                return False
        return True

    def match(self, *words):
        """ Consumes the current tokens if they match all the given words. Returns whether there was a match. """
        if not self.check(*words):
            return False
        self.index += len(words)
        return True

    def expect(self, *words):
        """ Consumes the current tokens if they match all the given words. Returns True if there was a match, raises a syntax error otherwise. """
        for i, word in enumerate(words):
            token = self.pop()
            if token.text != word:
                self.raise_syntax_error(token)
        return True

    def node(self, name, token):
        return {
            'node': name,
            'position': token.position,
        }

    def expr_node(self, name, token):
        return {
            **self.node(name, token),
            'op': self.op_node(token),
        }

    def op_node(self, token):
        return {
            'position': token.position,
            'text': token.text,
        }

    @contextmanager
    def try_parse(self, backtrack=False):
        index = self.index
        try:
            yield
            if backtrack:
                self.index = index
        except err:
            self.index = index

    def parse_program(self):
        token = self.peek()
        stmts = []
        while not self.eof():
            stmts.append(self.parse_stmt())
            self.expect(';')
        return {
            **self.node('Block', token),
            'stmts': stmts,
        }

    def parse_block(self):
        token = self.peek()
        stmts = []
        self.expect('{')
        while not self.check('}'):
            stmts.append(self.parse_stmt())
            self.expect(';')
        self.expect('}')
        return {
            **self.node('Block', token),
            'stmts': stmts,
        }

    def parse_stmt(self):
        token = self.pop()

        if token.text == 'use':
            return {
                **self.node('StmtUse', token),
                'name': self.parse_id(),
                'detail': self.match('hiding') and ['hiding', *self.parse_id_list()] or ['all'],
            }
        if token.text == 'skip':
            return {
                **self.node('StmtSkip', token),
            }
        if token.text == 'print':
            return {
                **self.node('StmtPrint', token),
                'exprs': [] if self.check(';') else self.parse_expr_list(),
            }
        if token.text == 'return':
            return {
                **self.node('StmtReturn', token),
                'expr': None if self.check(';') else self.parse_tuple_expr(),
            }
        if token.text == 'yield':
            return {
                **self.node('StmtYield', token),
                'expr': self.parse_tuple_expr(),
            }
        if token.text == 'if':
            exprs = [self.parse_tuple_expr()]
            self.expect('do')
            blocks = [self.parse_block()]
            while self.match(';', 'elif'):
                exprs.append(self.parse_tuple_expr())
                self.expect('do')
                blocks.append(self.parse_block())
            if self.match(';', 'else'):
                self.expect('do')
                blocks.append(self.parse_block())
            return {
                **self.node('StmtIf', token),
                'exprs': exprs,
                'blocks': blocks,
            }
        if token.text in {'while', 'until'}:
            return {
                **self.node(f'Stmt{token.text.capitalize()}', token),
                'kind': token.text,
                'expr': self.parse_tuple_expr(),
                'label': self.match('label') and self.parse_id() or None,
                'block': self.expect('do') and self.parse_block(),
            }
        if token.text == 'for':
            return {
                **self.node('StmtFor', token),
                'vars': self.parse_for_loop_var_list(),
                'iterables': self.expect('in') and self.parse_expr_list(),
                'label': self.match('label') and self.parse_id() or None,
                'block': self.expect('do') and self.parse_block(),
            }
        if token.text in {'break', 'continue'}:
            return {
                **self.node('StmtLoopControl', token),
                'stmt': token.text,
                'label': None if self.check(';') else self.parse_id(),
            }
        if token.text == 'func':
            return {
                **self.node('StmtFunc', token),
                **self.parse_func_header(),
                'block': self.match('def') and self.parse_block() or self.expect('extern') and None,
            }
        if token.text == 'class':
            return {
                **self.node('StmtClass', token),
                'id': self.parse_id(),
                'base': self.match('(') and (self.parse_type(), self.expect(')'))[0] or None,
                'members': self.expect('def') and self.parse_class_member_list(),
            }
        self.backtrack()  # backtrack if no keyword has been matched

        if token.type == Token.ID and self.peek(1).text == ':':
            return {
                **self.node('StmtDecl', token),
                'id': self.parse_id(),
                'type': self.expect(':') and self.parse_type() or None,
                'expr': self.match('=') and self.parse_tuple_expr() or None,
            }

        exprs = [self.parse_tuple_expr()]
        op_token = self.pop()
        for op in ASSIGNMENT_OPERATORS:
            if op_token.text == op:
                return {
                    **self.expr_node('StmtAssgExpr', Token(op[:-1], op_token.type, op_token.position)),
                    'position': token.position,
                    'exprs': [exprs[0], self.parse_tuple_expr()],
                }
        self.backtrack()  # backtrack if no assignment operator has been matched

        while self.match('='):
            exprs.append(self.parse_tuple_expr())
        return {
            **self.node('StmtAssg', token),
            'exprs': exprs,
        }

    def parse_class_member_list(self):
        members = []
        self.expect('{')
        while not self.check('}'):
            members.append(self.parse_class_member())
            self.expect(';')
        self.expect('}')
        return members

    def parse_class_member(self):
        token = self.pop()

        if token.text == 'func':
            return {
                **self.node('ClassMethod', token),
                **self.parse_func_header(),
                'block': self.match('def') and self.parse_block() or self.expect('abstract') and None,
            }
        if token.text in {'constructor', 'destructor'}:
            return {
                **self.node(f'Class{token.text.capitalize()}', token),
                'id': f'<{token.text}>',
                'args': [],
                'ret': {
                    **self.node('TypeName', token),
                    'name': 'Void',
                },
                'block': self.expect('def') and self.parse_block(),
            }
        self.backtrack()  # backtrack if no keyword has been matched

        return {
            **self.node(f'ClassField', token),
            'id': self.parse_id(),
            'type': self.expect(':') and self.parse_type() or None,
            'default': self.match('=') and self.parse_tuple_expr() or None,
        }

    def parse_func_header(self):
        return {
            'generator': self.match('*'),
            'id': self.parse_id(),
            'typevars': self.match('<') and (self.parse_id_list(), self.expect('>'))[0] or [],
            'args': self.parse_func_arg_list(),
            'ret': self.match(':') and self.parse_type() or None,
        }

    def parse_func_arg_list(self):
        args = []
        self.expect('(')
        while not self.check(')'):
            args.append(self.parse_func_arg())
            if not self.match(','):
                break
        self.expect(')')
        return args

    def parse_func_arg(self):
        return {
            **self.node('FuncArg', self.peek()),
            'variadic': self.match('...'),
            'name': self.parse_id(),
            'type': self.match(':') and self.parse_type() or None,
            'default': self.match('=') and self.parse_expr() or None,
        }

    def parse_id_list(self):
        ids = [self.parse_id()]
        while self.match(','):
            ids.append(self.parse_id())
        return ids

    def parse_id(self):
        token = self.pop()
        if token.type != Token.ID:
            self.raise_syntax_error(token)
        return token.text

    def parse_interpolation_expr(self):
        expr = self.parse_tuple_expr()
        if not self.eof():
            self.raise_syntax_error(self.peek())
        return expr

    def parse_tuple_expr(self):
        token = self.peek()
        exprs = self.parse_expr_list()
        if len(exprs) == 1:
            return exprs[0]
        return {
            **self.expr_node('ExprTuple', token),
            'exprs': exprs,
        }

    def parse_expr_list(self):
        exprs = [self.parse_expr()]
        while self.match(','):
            exprs.append(self.parse_expr())
        return exprs

    def parse_expr(self, precedence=0):
        # When calling `parse_expr()` recursively, the `precedence` argument should be equal to the precedence of the
        # recently parsed operator, if it's left-associative, or that precedence minus one, if it's right-associative.
        token = self.pop()
        expr = self.parse_expr_prefix_op(token)

        while EXPR_OPERATOR_PRECEDENCE[Fixity.NON_PREFIX, self.peek().text] > precedence:
            expr = self.parse_expr_non_prefix_op(expr, self.pop())
            expr['position'] = token.position

        return expr

    def parse_expr_prefix_op(self, token):
        if token.type == Token.ID:
            return {
                **self.expr_node('AtomPlaceholder' if token.text == '_' else 'AtomId', token),
                'id': token.text,
            }
        if token.type == Token.NUMBER:
            text = token.text.replace('_', '').lower()
            if any(text.startswith(prefix) for prefix in ['0b', '0o', '0x']):
                bases = {'b': 2, 'o': 8, 'x': 16}
                value = int(text, bases[text[1]])
            elif any(c in text for c in 'ef'):
                value = float(text.replace('f', ''))
            elif any(c in text for c in '.r'):
                value = text.replace('r', '')
            else:
                value = int(text)
            return {
                **self.expr_node('AtomInt' if isinstance(value, int) else 'AtomFloat' if isinstance(value, float) else 'AtomRat', token),
                'value': value,
            }
        if token.text in {'false', 'true'}:
            return {
                **self.expr_node('AtomBool', token),
                'value': token.text == 'true',
            }
        if token.type in {Token.CHAR, Token.STRING}:
            return {
                **self.expr_node(f'Atom{token.type.capitalize()}', token),
                'value': token.text[1:-1],
            }
        if token.text in {'null', 'super', 'this'}:
            return {
                **self.expr_node(f'Atom{token.text.capitalize()}', token),
            }
        if token.text == '(':  # grouping
            return {
                **self.parse_tuple_expr(),
                '_parenthesized': self.expect(')'),
            }
        if token.text in {'[', '{'}:  # containers
            closing_bracket = chr(ord(token.text) + 2)
            items = []
            kind = 'array'
            if token.text == '{' and self.match(':'):
                kind = 'dict'
            else:
                if token.text == '{':
                    kind = 'set'
                    with self.try_parse(backtrack=True):
                        if self.match('...:') or self.parse_expr() and self.match(':'):
                            kind = 'dict'
                while not self.check(closing_bracket):
                    if kind in {'array', 'set'}:
                        items.append(self.parse_expr())
                    elif kind == 'dict':
                        items.append(self.parse_dict_item())
                    if not self.match(','):
                        if not self.check(closing_bracket) and len(items) == 1 and items[0]['node'] != 'DictSpread':
                            comprehensions = []
                            while self.check('for') or self.check('if'):
                                comprehensions.append(self.parse_comprehension())
                            return {
                                **self.expr_node('ExprComprehension', token),
                                'kind': kind,
                                'exprs': items[0]['exprs'] if items[0]['node'] == 'DictPair' else items,
                                'comprehensions': (comprehensions, self.expect(closing_bracket))[0],
                            }
                        break
            return {
                **self.expr_node('ExprCollection', token),
                'kind': kind,
                'items': (items, self.expect(closing_bracket))[0],
            }
        if token.text in {'+', '-', 'not'}:  # prefix operators
            return {
                **self.expr_node('ExprUnaryOp', token),
                'expr': self.parse_expr(EXPR_OPERATOR_PRECEDENCE[Fixity.PREFIX, token.text]),
            }
        if token.text == '...':  # spread operator
            return {
                **self.expr_node('ExprSpread', token),
                'expr': self.parse_expr(EXPR_OPERATOR_PRECEDENCE[Fixity.PREFIX, token.text]),
            }
        if token.text == 'lambda':
            return {
                **self.expr_node('ExprLambda', token),
                'ids': [] if self.check(':') else self.parse_id_list(),
                'expr': self.expect(':') and self.parse_expr(EXPR_OPERATOR_PRECEDENCE[Fixity.PREFIX, token.text]),
            }
        self.raise_syntax_error(token)

    def parse_expr_non_prefix_op(self, left, token):
        if token.text in {'.', '?.'}:  # attribute access
            return {
                **self.expr_node('ExprAttr', token),
                'expr': left,
                'safe': token.text.startswith('?'),
                'attr': self.parse_id(),
            }
        if token.text in {'[', '?['}:  # element access
            safe = token.text.startswith('?')
            if not safe:
                slice = None
                with self.try_parse():
                    exprs = [None] * 3
                    with self.try_parse():
                        exprs[0] = self.parse_expr()
                    self.expect(':')
                    with self.try_parse():
                        exprs[1] = self.parse_expr()
                    with self.try_parse():
                        self.expect(':')
                        with self.try_parse():
                            exprs[2] = self.parse_expr()
                    slice = exprs
                if slice:
                    return {
                        **self.expr_node('ExprSlice', token),
                        'expr': left,
                        'slice': (slice, self.expect(']'))[0],
                    }
            return {
                **self.expr_node('ExprIndex', token),
                'safe': safe,
                'exprs': [left, (self.parse_tuple_expr(), self.expect(']'))[0]],
            }
        if token.text in {'(', '@('}:  # function call
            args = []
            while not self.check(')'):
                args.append(self.parse_call_arg())
                if not self.match(','):
                    break
            self.expect(')')
            return {
                **self.expr_node('ExprCall', token),
                'expr': left,
                'args': args,
                'partial': token.text.startswith('@'),
            }
        if token.text in {'!'}:  # postfix operators
            return {
                **self.expr_node('ExprUnaryOp', token),
                'expr': left,
            }
        if token.text in {'^', '^^', '??', 'and', 'or'}:  # right-associative infix operators
            return {
                **self.expr_node('ExprBinaryOp', token),
                'exprs': [left, self.parse_expr(EXPR_OPERATOR_PRECEDENCE[Fixity.NON_PREFIX, token.text] - 1)],
            }
        if token.text in {'/', '//', '%', '*', '&', '+', '-', '%%'}:  # left-associative infix operators
            return {
                **self.expr_node('ExprBinaryOp', token),
                'exprs': [left, self.parse_expr(EXPR_OPERATOR_PRECEDENCE[Fixity.NON_PREFIX, token.text])],
            }
        if token.text in {'...', '..'}:  # range operators
            exprs = [left]
            with self.try_parse():  # infinite range if no second expression
                exprs.append(self.parse_expr(EXPR_OPERATOR_PRECEDENCE[Fixity.NON_PREFIX, token.text]))
            inclusive = token.text == '..'
            if len(exprs) == 1 and inclusive:
                self.raise_syntax_error(token)
            return {
                **self.expr_node('ExprRange', token),
                'exprs': exprs,
                'inclusive': inclusive,
            }
        if token.text == 'by':
            return {
                **self.expr_node('ExprBy', token),
                'exprs': [left, self.parse_expr(EXPR_OPERATOR_PRECEDENCE[Fixity.NON_PREFIX, token.text])],
            }
        if token.text in {'==', '!=', '<', '<=', '>', '>='}:  # comparison operators
            right = self.parse_expr(EXPR_OPERATOR_PRECEDENCE[Fixity.NON_PREFIX, token.text] - 1)
            chained = right['node'] == 'ExprCmp' and not right.get('_parenthesized')
            return {
                **self.expr_node('ExprCmp', token),
                'exprs': [left, *right['exprs']] if chained else [left, right],
                'ops': [self.op_node(token), *right['ops']] if chained else [self.op_node(token)],
            }
        if token.text == 'in' or token.text == 'not' and self.match('in'):  # `in` / `not in`
            return {
                **self.expr_node('ExprIn', token),
                'exprs': [left, self.parse_expr(EXPR_OPERATOR_PRECEDENCE[Fixity.NON_PREFIX, token.text])],
                'not': token.text == 'not',
            }
        if token.text == 'is':  # `is null` / `is not null`
            return {
                **self.expr_node('ExprIsNull', token),
                'expr': left,
                'not': (self.match('not'), self.expect('null'))[0],
            }
        if token.text == '?':  # ternary conditional operator
            return {
                **self.expr_node('ExprCond', token),
                'exprs': [left, self.parse_expr(), self.expect(':') and self.parse_expr(EXPR_OPERATOR_PRECEDENCE[Fixity.NON_PREFIX, token.text] - 1)],
            }
        # No syntax error here since `EXPR_OPERATOR_PRECEDENCE` is 0 for unknown operators anyway.

    def parse_dict_item(self):
        token = self.peek()

        if self.match('...:'):
            return {
                **self.expr_node('DictSpread', token),
                'expr': self.parse_expr(),
            }
        return {
            **self.node('DictPair', token),
            'exprs': [self.parse_expr(), self.expect(':') and self.parse_expr()],
        }

    def parse_comprehension(self):
        token = self.pop()

        if token.text == 'for':
            return {
                **self.node('ComprehensionIteration', token),
                'vars': self.parse_for_loop_var_list(),
                'iterables': self.expect('in') and self.parse_expr_list(),
            }
        if token.text == 'if':
            return {
                **self.node('ComprehensionPredicate', token),
                'expr': self.parse_tuple_expr(),
            }

    def parse_for_loop_var_list(self):
        # We could use `parse_expr_list` instead, but there is a problem with ambiguity of `in` token.
        vars = [self.parse_for_loop_var()]
        while self.match(','):
            vars.append(self.parse_for_loop_var())
        return vars

    def parse_for_loop_var(self):
        token = self.pop()
        if token.type == Token.ID:
            return self.parse_expr_prefix_op(token)
        if token.text == '(':
            return {
                **self.expr_node('ExprTuple', self.peek()),
                'exprs': self.parse_for_loop_var_list(),
                '_parenthesized': self.expect(')'),
            }
        self.raise_syntax_error(token)

    def parse_call_arg(self):
        token = self.peek()
        return {
            **self.node('CallArg', token),
            'name': (self.parse_id(), self.expect('='))[0] if token.type == Token.ID and self.peek(1).text == '=' else None,
            'expr': self.parse_expr(),
        }

    def parse_type(self, precedence=0):
        # When calling `parse_type()` recursively, the `precedence` argument should be equal to the precedence of the
        # recently parsed operator, if it's left-associative, or that precedence minus one, if it's right-associative.
        type = self.parse_type_prefix_op(self.pop())

        while TYPE_OPERATOR_PRECEDENCE[self.peek().text] > precedence:
            type = self.parse_type_non_prefix_op(type, self.pop())

        return type

    def parse_type_prefix_op(self, token):
        if token.type == Token.ID:
            return {
                **self.node('TypeName', token),
                'name': token.text,
            }
        if token.text == '(':  # grouping
            if self.match(')') and self.check('->'):  # function without arguments
                return None
            return {
                **self.parse_type(),
                '_parenthesized': self.expect(')'),
            }
        if token.text in {'[', '{'}:  # containers
            closing_bracket = chr(ord(token.text) + 2)
            subtypes = [self.parse_type()]
            kind = 'array'
            if token.text == '{':
                if self.match(':'):
                    kind = 'dict'
                    subtypes.append(self.parse_type())
                else:
                    kind = 'set'
            return {
                **self.node('TypeCollection', token),
                'kind': kind,
                'subtypes': (subtypes, self.expect(closing_bracket))[0],
            }
        self.raise_syntax_error(token)

    def parse_type_non_prefix_op(self, left, token):
        if token.text == '?':  # nullable
            return {
                **self.node('TypeNullable', token),
                'subtype': left,
            }
        if token.text == '*':  # tuple
            right = self.parse_type(TYPE_OPERATOR_PRECEDENCE[token.text] - 1)
            chained = right['node'] == 'TypeTuple' and not right.get('_parenthesized')
            return {
                **self.node('TypeTuple', token),
                'types': [left, *right['types']] if chained else [left, right],
            }
        if token.text == '->':  # function
            right = self.parse_type(TYPE_OPERATOR_PRECEDENCE[token.text] - 1)
            chained = right['node'] == 'TypeFunc' and not right.get('_parenthesized')
            left = [] if left is None else [left]
            return {
                **self.node('TypeFunc', token),
                'types': [*left, *right['types']] if chained else [*left, right],
            }
        # No syntax error here since `TYPE_OPERATOR_PRECEDENCE` is 0 for unknown operators anyway.
