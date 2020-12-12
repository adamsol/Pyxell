
# Manual

Pyxell [_pixel_] is a multi-paradigm, statically typed programming language, compiled to machine code via C++.

This manual should let you quickly learn all the details to start programming in Pyxell.
It is assumed that you already know some programming language (preferably Python), since basic programming concepts are not explained here.

You are encouraged to run the code snippets and experiment with them for yourself.
To run Pyxell code, go to the [Playground](/playground.md),
clone the repository and follow the instructions on [Github](https://github.com/adamsol/Pyxell#requirements),
or download Windows binaries from the [Releases](https://github.com/adamsol/Pyxell/releases).


## Hello, world!

If you can run the following code and see the message on the screen, you are ready to start.

```
print "Hello, world!"
```


## Variables and types

### Variable declaration

Pyxell is statically typed. Variables have types assigned during compilation.
In most cases, type of an expression is automatically inferred and the value can be directly assigned to a variable.

```
x = 1
```

In other cases, when the type cannot be inferred or you want to declare a variable without initializing it, you can set the type explicitly.
When not directly initialized, variable is automatically initialized with the default value for a given type.
You can find the list of all available types and their default values in the [Specification](/specification.md#types).

```
y: Bool
```

Variable name must start with a letter or underscore, but may also contain digits and apostrophes.
Once a variable has been created, its type cannot be changed.

### Type coercion

Values of some types can be automatically converted to more general types: `Int -> Rat -> Float` or `Char -> String`.

```
x: Float = 1
```

The coercion doesn't work in the other direction.

```
y: Int = 1.0  # error: No implicit conversion from `Rat` to `Int`.
```


## Arithmetic and logic

### Numbers

Standard integers in Pyxell have 64 bits of precision and range from `-2^63` to `2^63-1`.
Binary, octal, and hexadecimal literals are supported.

```
print 10, 0b101, 0o36, 0xAF
```

Rational numbers have unlimited precision.
They can be written either as integers with `r` suffix, or non-integers in decimal form.
They are also created as the result of division or exponentiation
(to obtain an integer from a division or exponentiation, use lossy `//` and `^^` operators).

```
print 1r
print 0.1 + 1/5
print 4^-2
```

You can retrieve the numerator and denominator from a rational number.

```
print 0.75.fraction
```

Floating-point numbers have 64 bits of precision and follow the IEEE 754 standard.
They can be written with `f` suffix or in scientific notation.

```
print 0.5f
print 129e+40
```

Underscores can be additionally used in all numeric literals, to enhance readability of long numbers.

```
print 1_000_000
```

### Boolean values

There are two boolean values: `true` and `false`.
Logical negation and short-circuiting conjunction and disjunction operators are available.

```
print not true
print true and false
print true or false
```

Boolean values are most often obtained in the result of comparisons.
When comparison operators are chained, they behave as if connected with `and` operator.

```
print -2 < 1.5 == 3/2 <= 1e1
```


## Characters and strings

### Characters

Characters are written in single quotes.

```
c = 'A'
```

You can get character's ASCII code, as well as obtain character corresponding to a given integer.

```
print c.code
print 90.char
```

You can also perform some arithmetic operations on characters.

```
print 'A' + 3
print '5' - '0'
```

### Strings

Strings are immutable sequences of characters. They are written in double quotes.

```
s = "qwerty"
```

You can access string's length, as well as its individual characters. Negative indexing and slicing is also supported, like in Python.

```
print s.length
print s[0]
print s[-2]
print s[1:3]
```

Strings can be concatenated with `+` operator and repeated with `*` operator.

```
print s + "uiop", s * 2
```

You can construct formatted strings using interpolation syntax.

```
n = 7
print "{s} {4*n}"
```


## Control flow

Pyxell uses indentation-based syntax, similar to Python's. Only spaces are allowed (tab character will cause a syntax error).
Rather than `:` character, Pyxell uses `do` keyword for indicating beginning of a block, and `def` keyword for function and class definitions.
The scope of a variable declared in a block is limited to that block.

### `if` statement

The first branch whose condition evaluates to `true` is executed.

```
if 2 + 2 > 4 do
    print false
elif 2 + 2 == 4 do
    print true
else do
    print false
```

### `while` loop

The loop runs while the condition is satisfied.

```
a = 0
while a < 5 do
    a += 1
print a
```

### `until` loop

This loop is similar to `while` loop, but it is always executed at least once and runs until the condition is satisfied.

```
a = 0
until a %% 5 do
    a += 1
print a
```

### `for` loop

It can be used to loop over ranges (of numbers or characters) and other iterables.
Range can be inclusive (`a..b`), exclusive (`a...b`), or infinite (`a...`).

```
for x in 1..5 do
    print x
```

You can optionally provide a step value, which can be either positive or negative (it is 1 by default).

```
for x in "abcd" by -2 do
    print x
```

It is possible to loop over multiple iterables at once and provide custom step values to any of them.

```
for x, c in 0.5... by -0.1, 'A'...'D' do
    print x, c
```

### `continue` and `break`

You can use these statements to exit the current iteration or the whole loop.

```
for i in 1..10 do
    if i %% 2 do
        continue
    if i > 5 do
        break
    print i
```

Labels are also supported. This can be useful for breaking out of nested loops.

```
n = 30
for x in 1..n label loop do
    for y in 1..x do
        if x * y == n do
            print "{n} = {x} * {y}"
            break loop
```

### Empty blocks

To create an empty block of code, use `skip` statement, so that the program can be correctly parsed.

```
if false do
    skip
else do
    print true
```

### Comments

Pyxell supports both single-line and multiline comments.

```
# single-line comment
{#
multiline
comment
#}
```


## Containers

### Arrays

Arrays are similar to strings, but they are mutable and can have elements of any type.

```
a = [5, 8, 6]
print a.length
print a[0]
print a[-1]
print a[2::-2]
```

Containers have reference semantics, so they are not implicitly copied when variables are passed.
Mutation of one instance is reflected in all other instances of the same container.

```
b = a
b[0] = 10
print a[0]
```

When an empty container is created, its type must be explicitly given.
Empty literals can be skipped in variable declarations, since this is the default value.

```
e: [Char]  # = []
print e
```

Arrays can be concatenated, repeated, and compared using standard operators.

```
print [2, 3] + [4]
print [0] * 10
print [false, true] < [true]
```

You can use array comprehension, as well as range literals and spread operator with optional step.

```
print [x*y for x in 1..3 for y in x..3]
print ['$', 'a'..'g' by 2, ..."xyz"]
```

For type safety, containers in Pyxell are invariant, which means they cannot be implicitly converted to another type,
even if types of the elements match (see [here](https://stackoverflow.com/q/2745265) for a broader explanation).
However, container literals can be automatically converted.

```
c: [Rat]
c = [...a]  # copy of the array of Int, elements converted to Rat
c = a  # error: No implicit conversion from `[Int]` to `[Rat]`.
```

### Sets

Sets contain no duplicates and do not preserve order of elements.

```
print {3, 4, 4}
```

To check if an element is in the set, use `in` operator.

```
print 'b' in {'a', 'b'}
```

There exist operators for set union, difference, and intersection.

```
a = {1, 2}
b = {2, 3}
print a + b, a - b, a & b
```

Like with arrays, you can use comprehensions, ranges, and spread syntax to create sets.

```
print {i//2 for i in 0...4}
print {..."test"}
```

Containers are not hashable, so they cannot be stored in sets.

```
{[false]}  # error: Type `[Bool]` is not hashable.
```

### Dictionaries

Dictionaries are hash maps. Like sets, they do not preserve order of elements.
They work similarly to `defaultdict` in Python: if a key is not present, the default value for a given type is automatically created in the dictionary.

```
d = {"abc": 3}
print d["abc"]
print d[""]
```

Use `in` operator for checking if the dictionary contains a given key.

```
print "abc" in d
```

Dictionaries can be merged with `+` operator. In the case of repeated keys, the second value wins.

```
print {1: false} + {1: true}
```

Dictionary comprehension works similarly to array and set comprehension.

```
print {c: c.code for c in 'A'..'Z' by 5}
```

When iterated over, dictionaries produce pairs of key and value.

```
for k, v in d do
    print k, v
```

Spread operator for dictionaries consists of an extra colon.

```
print {...d}   # set of key-value pairs from the dictionary
print {...:d}  # copy of the dictionary
```


## Nullable types

To accept `null` value, variable's type must be explicitly marked as nullable.

```
b: Bool?
b = true
b = null
print b
```

You can either directly check if a value is `null`, or use special coalescing and conditional operators.

```
a: [Int]?
print a is null
print a ?? []
print a?.length
print a?[0]
```

There is also an operator to directly retrieve the value in cases when it is certainly not null.

```
x: Rat? = 1.5
print x! * 2
```


## Tuples

Two or more values separated with a comma form a tuple.

```
t = 1, 'Z'
print t
```

In some cases, like container literals or function calls, it is necessary to provide additional parentheses.

```
print [(true, "")]
```

Values can be retrieved using alphabetical properties or tuple destructuring (unneeded part can be discarded with an underscore).

```
print t.a
_, b = t
print b
```

Tuples are mutable, but they have value semantics, so they are hashable and can be passed around as if they were immutable.

```
s = {t}
t.a = 0
print t  # will print the new value
print s  # the set contains the original value
```


## Functions

### Function definition and call

Basic definition of a function consists of its name, list of arguments, return type, and body.

```
func square(x: Int): Int def
    return x ^^ 2

print square(5)
```

When a function does not return anything, the return type should be `Void`.

```
func hello(): Void def
    print "Hello, world!"

hello()
```

Just like with variables, type annotations in functions are optional.
If omitted, a generic function, which can work with values of any type, will be created.
Generic functions are described in more detail in the next section.

```
func double(x) def
    return x * 2

print double(1)
print double("text")
```

You can provide default values for optional arguments.
The expressions will be evaluated every time the function is called (if they are needed), so mutable container literals can be safely used.

```
func push(x: Int, a: [Int] = []) def
    a.push(x)
    return a

print push(0)
print push(1)
print push(2, [3])
```

Arguments can be also passed in any order using their names.

```
func pow(base, exponent) def
    return base ^ exponent

print pow(exponent=-3, base=6)
```

Variadic functions are supported too. This is just a syntactic sugar for passing an array.
Ranges and spread syntax can be used when such a function is called, just like with array literals.

```
func sum(...numbers: [Rat]): Rat def
    return numbers.reduce(_+_)

print sum()
a = [5.5]
print sum(...a, 42, 1..10)
```

Functions can be stored in variables, passed to other functions as arguments, etc.
However, when a function is converted to a variable, all information about its arguments except for their types is lost.

```
s: [Rat]->Rat = sum
print s([1, 2])
print s()  # error: Too few arguments.
```

### Generic functions

Generic functions are standard functions with additional type variables, which can be used just like normal types.
They are compiled independently for each combination of types they are called with.

```
func log<T>(x: T): Void def
    print "logged", x

log(3)
log("str")
```

Function declaration may contain default values for generic arguments, and the body may contain any code dependent on the real types.
Errors will be reported when the function cannot be compiled with given types.

```
func multiply<A,B,C>(a: A, b: B = 1): C def
    return a * b

print multiply(3, "qwerty")
print multiply({0.5f})  # error: No binary operator `*` defined for `{Float}` and `Int`.
```

When a type name is used more than once, the compiler will try to unify types of the arguments, following the coercion rules.

```
func contains<T>(a: [T], x: T): Bool def
    return x in a

print contains([3r], 3)  # T will be Rat
```

As described in the previous section, a generic function can also be created implicitly, by omitting the type annotations.

```
func contains2(a, x) def
    return x in a

print contains2("abc", 'd')
```

Note that for recursive functions to work, an explicit return type is necessary.

### Lambda functions

Lambda is an anonymous function, whose all arguments, as well as the return type, are generic.

```
double = lambda x: x * 2
print double(1/3)
```

You can use placeholder syntax to write even more concise functions. Each underscore corresponds to one argument.

```
div = _/_
print div(9, -12)
```

Placeholder resolving doesn't run through function calls by default (placeholders inside a function call form their own functions for corresponding arguments).
To create a partial function, add `@` character.

```
div_by_4 = div@(_, 4)  # without `@`, `_` would be an identity function
print div_by_4(10)
```

Note that when a function is passed to another function, its type must be known.
For example, you cannot pass a lambda function to another lambda function.
In the case of functional arguments, it's best to use the full generic definition.

```
func apply<A,B>(f: A->B, x: A): B def
    return f(x)

print apply(3*_, 14)
```

### Generators

Generator is a function producing a sequence of values that can be iterated over without storing it in memory.
To create a generator, add an asterisk symbol to the function definition.

```
func* range(n: Int): Int def
    for i in 0...n do
        yield i

print [...range(5)]
```

Generic functions can be generators as well.

```
func* reversed(a) def
    for x in a by -1 do
        yield x

a = [4, -1, 0.6]
print [...reversed(a)]
```

Note that generators are currently supported only with Clang.


## Classes

### Class definition and object construction

Definition of a class consists of its name and list of fields.
Each field may have an explicit default value; if not provided, it will be the default value for a given type.

```
class Cat def
    name: String
    afraid_of_water: Bool = true
```

Every class has a default constructor function that accepts field values in the order of definition, or as named arguments.
Fields not directly initialized will receive their default values.

```
cat = Cat(name="Simba")
print cat.name, cat.afraid_of_water
```

Remember that class objects must always be explicitly constructed before use (they have no valid default value).
The following code will crash (or raise a proper exception, once they are implemented).

```
cat': Cat
cat'.name = "Simba"  # SIGSEGV
```

### Methods

Methods are similar to normal functions, but are called in the context of an object.

```
class Vector def
    x: Float
    y: Float

    func length(): Float def
        return math.sqrt(this.x^2 + this.y^2)

print Vector(5, 12).length()
```

Method is bound to the object before it is called, so it can be treated as a standard function.

```
class Multiplier def
    a: Int

    func resolve(b: Int): Int def
        return this.a * b

r = Multiplier(10).resolve
print r(6)
```

If a special method `toString()` is defined in a class, it will be used to display objects of this class.

```
class Greeting def
    name: String

    func toString(): String def
        return "Hello, {this.name}!"

print Greeting("world")
```

Generic methods, like generic classes, are currently not supported.

### Constructors and destructors

Unlike in other popular programming languages, a custom constructor doesn't have any arguments.
It does not override the default constructor, but complements it.
It is executed immediately after the object has been created.

```
class IntWrapper def
    value: Int

    constructor def
        print "Created object with value {this.value}"

IntWrapper(-3)
```

Destructors are similar to constructors. Destructor is called when an object does not have any more references in the program.

```
class Resource def
    id: Int

    destructor def
        print "Resource {this.id} freed"

r = Resource(1)
print r.id
```

However, due to implementation details, the moment when a given object will be destroyed is currently not well defined
(objects may live longer than they should).

### Inheritance

Derived class inherits all base class's fields and methods.
Inherited constructors are called automatically before the constructor of the derived class.
Inherited destructors are called after the destructor of the derived class (in the reverse order).

```
class Base def
    x: Int

    constructor def
        print "Base constructor, x = {this.x}"

    destructor def
        print "Base destructor"

class Derived(Base) def
    y: Int

    constructor def
        print "Derived constructor, y = {this.y}"

    destructor def
        print "Derived destructor"

Derived(y=4)
```

Derived class object can be assigned to a parent class variable, but not the other way around.

```
base: Base = Derived()
derived: Derived = Base()  # error: No implicit conversion from `Base` to `Derived`.
```

When derived class has a method with the same name as in the parent class, which method will be called depends on the real type of the object, not its declared type.
Inside the method body, you can call the corresponding method of the parent class using `super` keyword.

```
class A def
    func f(x: Int): Void def
        print "A: {x}"

class B(A) def
    func f(x: Int): Void def
        print "B: {x}"
        super(x//2)

a: A = B()
a.f(42)
```

Methods can be abstract. If a class has any abstract methods, it cannot be instantiated.

```
class Abstract def
    func f() abstract

class Concrete(Abstract) def
    func f(): Void def
        print "ok"

Concrete().f()
Abstract().f()  # error: Cannot instantiate an abstract class `Abstract`.
```


## Modules

Pyxell's standard library consists of various functions and constants split into several modules.
You can find all of them in the [Specification](/specification.md#standard-library).

Functions from the main module are available globally.

```
print readInt() * 2  # remember to provide input to the program
print max("abc", "bc")
```

To access identifiers from other modules, use the module's name explicitly.

```
print math.cos(0)
```

There is also a `use` statement that imports all names from a module to the current scope.

```
use math
print PI, E
```

To avoid possible name conflicts, you can explicitly ignore some names from a module.

```
use math hiding exp
```

Note that creating custom modules is currently not supported.


## Examples

Here are some more code snippets to present Pyxell in action.

### Summing numbers from the standard input

```
s = 0r
while true do
    x = readRat()  # remember to provide input to the program
    if x == 0 do
        break
    s += x
print s
```

### Counting characters in a string

```
s = "abracadabra"
d: {Char:Int}
for c in s do
    d[c] += 1
print d
```

### Removing duplicates from an array

```
a = ["apple", "banana", "apple", "orange", "banana"]
b: [String]
v: {String}
for x in a do
    if x not in v do
        b.push(x)
        v.add(x)
print b
# Or, if the order of elements is not important, just:
print {...a}
```

### Factorial with lambda functions

```
factorial = [2r.._].reduce(_*_)
print factorial(10)
```

### Generator for Fibonacci numbers

```
func* fib() def
    a, b = 0r, 1r
    yield a
    while true do
        yield b
        a, b = b, a + b

print [x for x, _ in fib(), 0...10]
```

### 100 digits of π

```
# https://en.wikipedia.org/wiki/Bailey–Borwein–Plouffe_formula
pi = 0r
d = 1r
for k in 0..640 by 8 do
    pi += (4/(k+1) - 2/(k+4) - 1/(k+5) - 1/(k+6)) / d
    d *= 16
print pi.toString()[:102]
```

### Summing digits of a big number

```
print "{2^1000}".fold(_-'0'+_, 0)
```
