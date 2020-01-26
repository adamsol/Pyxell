
from contextlib import contextmanager
from pathlib import Path

import llvmlite.ir as ll

from .compiler import CustomIRBuilder, PyxellCompiler
from .types import *

abspath = Path(__file__).parents[1]


class BaseLibraryGenerator(PyxellCompiler):

    def __init__(self):
        self.builder = CustomIRBuilder()
        self.module = ll.Module()

        input_string_length_limit = 1023

        self.formats = {
            'int': self.declare_format('%lld'),
            'float_read': self.declare_format('%lg'),
            'float_write': self.declare_format('%.15g'),
            'float_write_int_dot_zero': self.declare_format('%.0f.0'),
            'bool_true': self.declare_format('true'),
            'bool_false': self.declare_format('false'),
            'char': self.declare_format('%c'),
            'string_read': self.declare_format(f'%{input_string_length_limit}s'),
            'string_read_line': self.declare_format(f'%{input_string_length_limit}[^\n]%*c'),
            'string_write': self.declare_format('%.*s'),
        }

        self.builtins = {
            func.name: func for func in [
                ll.Function(self.module, ll.FunctionType(tVoid, [tPtr()]), 'free'),
                ll.Function(self.module, ll.FunctionType(tPtr(), [tInt]), 'malloc'),
                ll.Function(self.module, ll.FunctionType(tVoid, [tPtr(), tPtr(), tInt]), 'memcpy'),
                ll.Function(self.module, ll.FunctionType(tInt, [tPtr()], var_arg=True), 'printf'),
                ll.Function(self.module, ll.FunctionType(tVoid, [tChar]), 'putchar'),
                ll.Function(self.module, ll.FunctionType(tInt, [tPtr()], var_arg=True), 'scanf'),
                ll.Function(self.module, ll.FunctionType(tInt, [tPtr(), tPtr()], var_arg=True), 'sprintf'),
                ll.Function(self.module, ll.FunctionType(tInt, [tPtr(), tPtr()], var_arg=True), 'sscanf'),
                ll.Function(self.module, ll.FunctionType(tInt, [tPtr()], var_arg=True), 'strlen'),
                ll.Function(self.module, ll.FunctionType(tPtr(), [tPtr(), tPtr(), tInt]), 'strncpy'),

                ll.Function(self.module, ll.FunctionType(tFloat, [tFloat]), 'exp'),
                ll.Function(self.module, ll.FunctionType(tFloat, [tFloat]), 'log'),
                ll.Function(self.module, ll.FunctionType(tFloat, [tFloat]), 'log10'),
                ll.Function(self.module, ll.FunctionType(tFloat, [tFloat, tFloat]), 'pow'),
                ll.Function(self.module, ll.FunctionType(tFloat, [tFloat]), 'sqrt'),
                ll.Function(self.module, ll.FunctionType(tFloat, [tFloat]), 'cos'),
                ll.Function(self.module, ll.FunctionType(tFloat, [tFloat]), 'sin'),
                ll.Function(self.module, ll.FunctionType(tFloat, [tFloat]), 'tan'),
                ll.Function(self.module, ll.FunctionType(tFloat, [tFloat]), 'acos'),
                ll.Function(self.module, ll.FunctionType(tFloat, [tFloat]), 'asin'),
                ll.Function(self.module, ll.FunctionType(tFloat, [tFloat]), 'atan'),
                ll.Function(self.module, ll.FunctionType(tFloat, [tFloat, tFloat]), 'atan2'),
                ll.Function(self.module, ll.FunctionType(tFloat, [tFloat]), 'fabs'),
                ll.Function(self.module, ll.FunctionType(tFloat, [tFloat]), 'ceil'),
                ll.Function(self.module, ll.FunctionType(tFloat, [tFloat]), 'floor'),
                ll.Function(self.module, ll.FunctionType(tFloat, [tFloat]), 'trunc'),

                ll.Function(self.module, ll.FunctionType(tInt, [tPtr(tInt)]), 'time'),
            ]
        }

        with self.define(tFunc([tArray(tChar)], tString), 'CharArray_asString') as func:
            self.builder.ret(func.args[0])
        with self.define(tFunc([tString], tArray(tChar)), 'String_toArray') as func:
            length = self.extract(func.args[0], 1)
            result = self.array(tChar, [], length)
            self.call_builtin('memcpy', self.extract(result, 0), self.extract(func.args[0], 0), length)
            self.builder.ret(result)

        with self.define(tFunc([tString]), 'write') as func:
            self.call_builtin('printf', self.get_format('string_write'), self.extract(func.args[0], 1), self.extract(func.args[0], 0))
            self.builder.ret_void()
        with self.define(tFunc([tString]), 'writeLine') as func:
            self.call_builtin('printf', self.get_format('string_write'), self.extract(func.args[0], 1), self.extract(func.args[0], 0))
            self.call_builtin('putchar', vChar('\n'))
            self.builder.ret_void()
        with self.define(tFunc([tInt]), 'writeInt') as func:
            self.call_builtin('printf', self.get_format('int'), func.args[0])
            self.builder.ret_void()
        with self.define(tFunc([tFloat]), 'writeFloat') as func:
            with self.builder.if_else(self.should_float_be_displayed_as_integer_dot_zero(func.args[0])) as (int, notint):
                with int:
                    self.call_builtin('printf', self.get_format('float_write_int_dot_zero'), func.args[0])
                with notint:
                    self.call_builtin('printf', self.get_format('float_write'), func.args[0])
            self.builder.ret_void()
        with self.define(tFunc([tBool]), 'writeBool') as func:
            self.call_builtin('printf', self.builder.select(func.args[0], self.get_format('bool_true'), self.get_format('bool_false')))
            self.builder.ret_void()
        with self.define(tFunc([tChar]), 'writeChar') as func:
            self.call_builtin('printf', self.get_format('char'), func.args[0])
            self.builder.ret_void()

        with self.define(tFunc([], tString), 'read') as func:
            result = self.array(tChar, [], vInt(input_string_length_limit+1))
            ptr = self.extract(result, 0)
            self.call_builtin('scanf', self.get_format('string_read'), ptr)
            self.insert(self.call_builtin('strlen', ptr), result, 1)
            self.builder.ret(result)
        with self.define(tFunc([], tString), 'readLine') as func:
            result = self.array(tChar, [], vInt(input_string_length_limit+1))
            ptr = self.extract(result, 0)
            self.call_builtin('scanf', self.get_format('string_read_line'), ptr)
            self.insert(self.call_builtin('strlen', ptr), result, 1)
            self.builder.ret(result)
        with self.define(tFunc([], tInt), 'readInt') as func:
            result = self.builder.alloca(tInt)
            self.call_builtin('scanf', self.get_format('int'), self.builder.bitcast(result, tPtr()))
            self.builder.ret(self.builder.load(result))
        with self.define(tFunc([], tFloat), 'readFloat') as func:
            result = self.builder.alloca(tFloat)
            self.call_builtin('scanf', self.get_format('float_read'), self.builder.bitcast(result, tPtr()))
            self.builder.ret(self.builder.load(result))
        with self.define(tFunc([], tChar), 'readChar') as func:
            result = self.builder.alloca(tChar)
            self.call_builtin('scanf', self.get_format('char'), self.builder.bitcast(result, tPtr()))
            self.builder.ret(self.builder.load(result))

        with self.define(tFunc([tInt], tFloat), 'Int_toFloat') as func:
            self.builder.ret(self.builder.sitofp(func.args[0], tFloat))
        with self.define(tFunc([tFloat], tInt), 'Float_toInt') as func:
            self.builder.ret(self.builder.fptosi(func.args[0], tInt))

        with self.define(tFunc([tInt], tString), 'Int_toString') as func:
            result = self.array(tChar, [], vInt(21))
            ptr = self.extract(result, 0)
            self.call_builtin('sprintf', ptr, self.get_format('int'), func.args[0])
            self.insert(self.call_builtin('strlen', ptr), result, 1)
            self.builder.ret(result)
        with self.define(tFunc([tFloat], tString), 'Float_toString') as func:
            result = self.array(tChar, [], vInt(25))
            ptr = self.extract(result, 0)
            with self.builder.if_else(self.should_float_be_displayed_as_integer_dot_zero(func.args[0])) as (int, notint):
                with int:
                    self.call_builtin('sprintf', ptr, self.get_format('float_write_int_dot_zero'), func.args[0])
                with notint:
                    self.call_builtin('sprintf', ptr, self.get_format('float_write'), func.args[0])
            self.insert(self.call_builtin('strlen', ptr), result, 1)
            self.builder.ret(result)

        with self.define(tFunc([tString], tInt), 'String_toInt') as func:
            # `sscanf` needs a null-terminated string, so we need to copy it and append '\0'.
            length = self.extract(func.args[0], 1)
            ptr = self.call_builtin('malloc', self.builder.add(length, vInt(1)))
            self.call_builtin('strncpy', ptr, self.extract(func.args[0], 0), length)
            self.builder.store(vChar('\0'), self.builder.gep(ptr, [length]))
            result = self.builder.alloca(tInt)
            self.call_builtin('sscanf', ptr, self.get_format('int'), self.builder.bitcast(result, tPtr()))
            self.call_builtin('free', ptr)
            self.builder.ret(self.builder.load(result))
        with self.define(tFunc([tString], tFloat), 'String_toFloat') as func:
            # `sscanf` needs a null-terminated string, so we need to copy it and append '\0'.
            length = self.extract(func.args[0], 1)
            ptr = self.call_builtin('malloc', self.builder.add(length, vInt(1)))
            self.call_builtin('strncpy', ptr, self.extract(func.args[0], 0), length)
            self.builder.store(vChar('\0'), self.builder.gep(ptr, [length]))
            result = self.builder.alloca(tFloat)
            self.call_builtin('sscanf', ptr, self.get_format('float_read'), self.builder.bitcast(result, tPtr()))
            self.call_builtin('free', ptr)
            self.builder.ret(self.builder.load(result))

        ll.GlobalVariable(self.module, tFunc([tFloat, tFloat], tFloat), 'f.Float_pow').initializer = self.builtins['pow']

        for name in ['exp', 'log', 'log10', 'sqrt', 'cos', 'sin', 'tan', 'acos', 'asin', 'atan', 'atan2', 'ceil', 'floor', 'trunc']:
            func = self.builtins[name]
            ll.GlobalVariable(self.module, tPtr(func.ftype), f'f.{name}').initializer = func

        with self.define(tFunc([tFloat], tInt), 'time') as func:
            self.builder.ret(self.call_builtin('time', vNull(tPtr(tInt))))

        # https://en.wikipedia.org/wiki/Linear_congruential_generator
        # https://stackoverflow.com/a/3958859/12643160
        rand_state = ll.GlobalVariable(self.module, tInt, 'rand_state')
        rand_state.initializer = tInt(0)
        with self.define(tFunc([tInt]), 'seed') as func:
            self.builder.store(func.args[0], rand_state)
            self.builder.ret_void()
        with self.define(tFunc([], tInt), 'rand') as func:
            state = self.builder.load(rand_state)
            state = self.builder.srem(self.builder.add(self.builder.mul(tInt(1103515245), state), tInt(12345)), tInt(2**31))
            self.builder.store(state, rand_state)
            self.builder.ret(self.builder.and_(self.builder.ashr(state, tInt(16)), tInt(0x7FFF)))

    def declare_format(self, string):
        const = ll.Constant.literal_array([vChar(c) for c in string + '\0'])
        array = ll.GlobalVariable(self.module, const.type, self.module.get_unique_name('format'))
        array.global_constant = True
        array.initializer = const
        return array

    @contextmanager
    def define(self, type, name):
        func = ll.Function(self.module, type.pointee, f'def.{name}')
        func_ptr = ll.GlobalVariable(self.module, type, f'f.{name}')
        func_ptr.initializer = func
        entry = func.append_basic_block('entry')
        self.builder.position_at_end(entry)
        yield func

    def get_format(self, name):
        return self.builder.gep(self.formats[name], [vInt(0), vInt(0)])

    def call_builtin(self, name, *args):
        return self.builder.call(self.builtins[name], args)

    def should_float_be_displayed_as_integer_dot_zero(self, value):
        return self.builder.and_(
            self.builder.fcmp_ordered('<', self.call_builtin('fabs', value), vFloat(1e15)),
            self.builder.fcmp_ordered('==', value, self.call_builtin('floor', value)))
