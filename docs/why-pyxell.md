
# Why Pyxell?

Pyxell combines code elegance and brevity with static typing and native execution speed.
It is currently well suited for short programs, e.g. solving algorithmic or mathematical problems.

Here you can find how Pyxell compares to languages that it is most similar to: Python and C++.
Some of the issues, especially those regarding C++, concern also other popular languages, such as Java or C#.


## Pyxell vs. Python

Even though Python is generally a well-designed language,
a closer look reveals that it misses some features and suffers from cases of surprising behaviour and inconsistencies.
Below is a list of things that may be considered advantageous in Pyxell.

### Range literals

Pyxell provides range literals that can be used for iteration or directly in containers: `[1..5]`.
Ranges can be inclusive (two dots) as well as exclusive (three dots), and can have an optional step (set with `by` keyword).

### Empty set literal

Pyxell provides literal notation for both empty set and empty dictionary: `{}` and `{:}`, respectively.

### Lambdas with placeholder syntax

Lambda expressions in Pyxell can be simplified with the placeholder syntax: `_+1` is equivalent to `lambda x: x + 1`.

### Static typing

While dynamic typing is often very convenient,
static typing detects errors before the program is run, serves as code documentation, and reduces possible pitfalls,
such as `{0} | {False}` (set union) producing `{0}` in Python (because `0 == False`).
Thanks to type inference in Pyxell, explicit variable declarations may be omitted in many situations.

### Rational numbers

Arbitrary-precision rational numbers are used in Pyxell as the default representation for non-integers,
so that equations like `0.1 + 1/5 == 0.3` are satisfied.
Faster floating-point arithmetic can still be used by writing numbers with `f` suffix or in scientific notation.

### Proper set operators precedence

Basic operations on sets (`+`, `-`, `&`) have more intuitive precedence in Pyxell,
so that expression `{1} + {2} - {1}` produces `{2}` as expected,
contrary to `{1} | {2} - {1}` producing `{1, 2}` in Python.

### Operators for nullable types

Pyxell allows `null` value only for variables whose type has been explicitly marked as nullable.
Null-coalescing and null-conditional operators (`??`, `?.`, `?[]`) make working with such types easier.

### Useful mutable default arguments

[Unintuitive behaviour of mutable default arguments in Python](https://stackoverflow.com/q/1132941) is a trap that many programmers fall into.
In Pyxell, default expressions in function arguments (and class fields) are evaluated every time the function is called (or an object created),
so that container literals can be safely used in default arguments without the risk of leaking the modified value into future function calls.

### Key-value iteration over dictionaries

Standard iteration over a dictionary in Pyxell produces pairs of key and value, not just keys.
Unneeded part can be discarded with `_`.

### Caret as exponentiation operator

Pyxell uses `^` as power operator, which is closer to the mathematical notation and used more commonly in mathematical software than `**`.
Exponentiation works exactly even for negative exponents, producing rational numbers.
There is also a separate, lossy `^^` operator, which produces standard integers.

### Numbers with leading zeroes

Pyxell allows for decimal integer literals starting with `0`,
which in Python 2 would denote octal numbers and in Python 3 cause a syntax error.

### Tuples versus arrays

There is a clear distinction between tuples and arrays in Pyxell.
Tuples are indexed using alphabetical properties, e.g. `tuple.a`, and are not iterable, but provide type safety.
Tuples are mutable, but since they have value semantics (whole tuple is copied rather than just reference), they can still be used e.g. as dictionary keys.

### Consistent augmented assignment operators

In Pyxell, `x += y` always means `x = x + y` (with only one evaluation of `x`),
so that `a += [42]` doesn't mutate the array, as would `a.extend([42])`, but creates a new one.

### Consistent naming

To avoid possible inconsistencies, such as `defaultdict` and `OrderedDict` in Python, all type names in Pyxell are capitalized (PascalCase).
Built-in constants (e.g. `true`) are lowercase, since they are closer to variables than to types.

### Non-discriminated global variables

Pyxell allows modifying global variables inside functions by default.
Python's requirement of using `global` keyword is most probably not what programmers coming from other languages expect,
and it also not completely consistent, since mutable global objects can be always mutated anyway.

### Methods instead of global functions

Pyxell avoids polluting global namespace in favor of properties and methods:
`a.length` rather than of `len(a)`, `a.filter(f)` rather than `filter(f, a)`, etc.

### `this` keyword

Pyxell doesn't require an explicit `self` argument in class method definitions, since it is too repetitive and easy to forget.
Instead, Pyxell follows the convention from other object-oriented programming languages and uses `this` as a keyword.

### Default class constructors

A class object in Pyxell can be initialized by providing values for any of its fields as positional or named arguments,
while the remaining fields will be initialized with their default values.
Custom constructor can be defined, but cannot have any arguments and will be called only as a hook after the object has been created.

### Superclass method call is not magic

[Bare `super()` in Python doesn't work inside container comprehensions](https://stackoverflow.com/q/31895302), causing a `TypeError` that is hard to understand.
Pyxell's implementation doesn't have this limitation.
The syntax is also simpler: just `super(arguments)` instead of `super().method(arguments)`.

### Apostrophes in identifiers

Following the convention from functional programming languages such as OCaml and Haskell, Pyxell permits `'` character in identifiers.

### Multiline comments

Pyxell has both single-line and multiline comments: `#` and `{# #}`, respectively.

### Automatic line continuations

Pyxell's compiler automatically recognizes line continuations, even when no brackets have been used,
so there is no need to put `\` character at the end of a line.

### Compilation to machine code

Programs written in Pyxell are transpiled to C++ and compiled to native machine code by a well-optimized compiler (Clang or GCC),
which makes the execution as fast as possible.


## Pyxell vs. C++

C++ is a very powerful language, but due to its long way from being just an extension of C,
it became almost unbearably verbose and complicated.
Pyxell aims to be just as performant, but also remain simple and intuitive.

### Container literals

Pyxell has a clean syntax for array, set, and dictionary literals, as well as comprehensions and ranges.

### First-class tuples

Tuples in Pyxell can be created with just a comma, and retrieving a value is as easy as writing a one-letter attribute.
Tuples can also be naturally used in sets and as keys in dictionaries, while in C++ they are not hashable by default.

### Keyword arguments

Functions in Pyxell can be called with named arguments, which makes for cleaner code and reduces the need for function overloading.

### Negative indexing and slicing

Pyxell allows for accessing elements of arrays and strings by indexing from the end: `a[-1]`,
as well as building subsequences using a flexible slice notation: `a[i:j:k]`.

### String interpolation

Pyxell implements interpolation syntax for easy string formatting: `"a = {a}"`.

### Euclidean modulo

Modulo operator in Pyxell is based on modular arithmetic, which matters for negative numbers: `-4 % 3` is `2`, not `-1`.

### Chained comparisons

Comparison operators in Pyxell behave like expected when chained: `0 <= x < 10` means `0 <= x and x < 10`.
In C++, although this construct is syntactically and semantically valid, it is useless: the exemplary expression will produce `true` for any number `x`.

### Functions instead of bitwise operators

Rarely used bitwise operators have been replaced with functions in Pyxell.
This frees up some operators for other use and solves problems with operator precedence, like `1 | 2 == 2` producing `1` in C++.

### Additional arithmetic operators

Pyxell uses `^` operator (or `^^`) for exponentiation and `%%` operator for divisibility testing.

### Passing objects by value of reference

Containers and class objects are never implicitly copied in Pyxell.
The semantics is similar to passing pointers (and Pyxell in fact uses C++'s smart pointers), but with all the boilerplate removed.

### Explicit class members

Pyxell requires explicit `this` keyword, so that it is clear whether you refer to a class field or a regular variable.

### Fixed evaluation order of arguments

Expressions in Pyxell are evaluated in the natural order, which in the case of function calls and operators of equal priority is from left to right.

### Significant indentation

The structure of your code in Pyxell corresponds to how it will work. No braces or semicolons are needed.


## Benchmark

A simplified version of an [algorithm for generating integer partitions](http://jeromekelleher.net/generating-integer-partitions.html)
has been run in Pyxell, C++, and Python.

The following execution times have been measured for `n = 100` (output: `190569292`).
Pyxell and C++ programs were compiled with `-O3` flag. Compilation times were not taken into account.

| Pyxell (GCC 7.2.0) | Pyxell (Clang 8.0.1) | C++ (GCC 7.2.0) | C++ (Clang 8.0.1) | Python (CPython 3.7.6) | Python (PyPy 3.7.9) |
| ------------------ | -------------------- | --------------- | ----------------- | ---------------------- | ------------------- |
| 0.32 s             | 0.53 s               | 0.35 s          | 0.36 s            | 49.4 s                 | 0.95 s              |

Pyxell code:

```
func partitions(n) def
    r = 0
    a = [0] * (n+1)
    k = 1
    a[1] = n
    while k != 0 do
        x = a[k-1] + 1
        y = a[k] - 1
        k -= 1
        while x <= y do
            a[k] = x
            y -= x
            k += 1
        a[k] = x + y
        r += 1
    return r

print partitions(readInt())
```

C++ code:

```cpp
#include <iostream>

int partitions(int n) {
    int r = 0;
    int *a = new int[n+1];
    for (int i = 0; i <= n; ++i) {
        a[i] = 0;
    }
    int k = 1;
    a[1] = n;
    while (k != 0) {
        int x = a[k-1] + 1;
        int y = a[k] - 1;
        k -= 1;
        while (x <= y) {
            a[k] = x;
            y -= x;
            k += 1;
        }
        a[k] = x + y;
        r += 1;
    }
    return r;
}

int main() {
    int n;
    std::cin >> n;
    std::cout << partitions(n);
}
```

Python code:

```python
def partitions(n):
    r = 0
    a = [0] * (n+1)
    k = 1
    a[1] = n
    while k != 0:
        x = a[k-1] + 1
        y = a[k] - 1
        k -= 1
        while x <= y:
            a[k] = x
            y -= x
            k += 1
        a[k] = x + y
        r += 1
    return r

print(partitions(int(input())))
```

Note that the differences in execution time between languages will depend on the code that is measured.
However, Pyxell should always be close to C++ in performance, and substantially faster than Python (even with PyPy).


## Known problems

No language is perfect. Here is a list of things that may considered bugs or inconveniences in Pyxell.

### Slow compilation

Pyxell is only as fast as the C++ code it generates.
Since the base library contains over a thousand lines of C++ code with extensive usage of high-level features,
compiling even the simplest programs may take a few seconds,
depending on the compiler used (Clang is generally faster than GCC in this regard) and optimization level.
The compilation time may grow quickly, as each line of Pyxell code often translates to many lines of C++ code.

Furthermore, there is a problem with slow parsing of Pyxell files.
This may be solved in the future by changing ANTLR target from Python to another language or using another parser generator.

### Limited integer precision

Although Pyxell has a built-in type for arbitrary-precision rational numbers,
standard integers have fixed 64-bit precision, so it's possible to cause an overflow when performing arithmetic operations on them.

`/` (division) and `^` (exponentiation) operators produce exact results,
but since rational numbers have some overhead, integer operators (`//` and `^^`) must be sometimes used to retain speed of calculations.

### Uninitialized objects

Pyxell initializes variables and class fields with default values (and appends a default `return` statement in functions),
but class objects have no default values and must be constructed explicitly.
Therefore it is possible to have an invalid object, which will result in a program crash when used.

Some programming languages perform static analysis to find variables that may be uninitialized.
However, since this problem is undecidable in general, any halting algorithm will result in false positives or false negatives.
That's why Pyxell makes no attempt to prohibit (or warn about) using such uninitialized objects and leaves that to the programmer instead.

Though this may seem as a problem similar to dealing with unexpected `null` values,
which Pyxell tries to solve, uninitialized variables are actually not so common.
Since it's not possible to handle them in any way, it makes no sense to pass them deliberately to another function or class like `null` values.
An uninitialized object is always a programming error that must be fixed on the caller side.

### No guaranteed moment of destructor call

Even though Pyxell internally uses C++'s smart pointers (i.e. reference counting) for memory management,
the exact moment of when an object will be destroyed is not well defined.
It depends mainly on whether a variable is global or declared inside a function.

It is only guaranteed that all destructors will be eventually called before the program ends, provided that there are no circular references
(and Pyxell currently doesn't detect such cases, so memory leaks are also possible).

### Partial closures

Closures in Pyxell are based on closures in C++ with variables captured by value.
This works differently than in Python and some other languages when non-local variables in nested functions are concerned.
The following code will print `1` and `0` instead of two `1`s:

```
func f() def
    x = 0

    func g() def
        x += 1
        print x

    g()
    print x

f()
```

For the expected result you might want to use a mutable object, e.g. an array with one element, or a global variable instead.
Also note that in Python you would need to mark the `x` variable in `g` definition as `nonlocal` for the above code to work at all (after syntax changes).
