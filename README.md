Pyxell
======

### Clear and easy to use multi-paradigm compiled programming language with static typing. ###

*Note: Up to version 0.6.0 the project was developed in Haskell with BNFC. Now it is being rewritten to Python and ANTLR.*


Motivation
----------

Do you like Python for its expressive and intuitive syntax, but miss static type checking and runtime speed of compiled languages?

Do you enjoy functional programming in Haskell, yet find it overly complicated and not exactly suitable for everyday use?

Do you keep looking back at C++ for its speed and power, though can't stand its verbosity and ugliness in comparison to modern languages?

That's why I started creating Pyxell -- to bring together the best features of different programming languages.


Examples
--------

```
func fib(Int n) Int def
    if n <= 0 do
        return 0
    a, b = 0, 1
    for i in 2..n do
        a, b = b, a + b
    return b
        
print fib(10)
```

```
a = [c for c in 'A'..'Z']
for x, i in a, 0... do
    print "a[{i}] = {x}" 
```

```
func fold<Any T>(T,T->T f, T a, [T] t) T def
    for x in t do
        a = f(a, x)
    return a

print fold(_*_, 1, [2, 3, 4])  -- factorial
```

```
class C def
    String? s

    constructor(String? s: null) def
        self.s = s 

c = C()
print c.s?.length
print c.s ?? "---"
```


Features
--------

* Python-like syntax with semantic indentation (+)
* Strongly static typing with partial type inference (+)
* Full compilation to machine code (+)
* 64-bit integers and double-precision floating-point numbers (+)
* Native tuples (+)
* Immutable strings (+)
* String interpolation (+)
* Mutable arrays (+)
* Extensive for-loops with ranges, steps, and zipping (+)
* Array comprehension (+)
* Slicing (+)
* First-class functions (+)
* Default and named arguments (+)
* Lambda expressions (+)
* Generic functions (+/-)
* Module system (+/-)
* Classes with safe references (+)
* Separate nullable types (+)
* Generic types
* Containers library
* Operator overloading
* Arbitrary-precision arithmetic
* Closures
* Coroutines
* Exception handling
* Multiple inheritance
* Automatic memory management
* Concurrency


Details
-------

* Type checker and LLVM compiler written in Haskell with BNFC.
* Compilation to machine code (and optimizations) with Clang.


Requirements
------------

These are the software versions that I use. Pyxell may work with others versions, but it is not guaranteed.

* ANTLR 4.7.2 (to build the parser)
* Python 3.7.4 with packages from `requirements.txt` installed (to run tests)

To compile and link a Pyxell program correctly, a C++ standard library is required for Clang.
This shouldn't be a problem on Linux, but on Windows this may not work out of the box.
In some cases Windows SDK installation may be required
or it may be necessary to run `pyxell` with `-target x86_64-pc-windows-gnu`
(run `test.py` with `-t` argument to use this).


Usage
-----

```
make libs
./pyxell.sh code.px
```

If the program is correct, `code.ll` file and an executable should be created in the same folder.
If not, errors will be displayed, pointing to the erroneous code location.

Run `make parser` to run ANTLR after changing the grammar (`src/Pyxell.g4`).
Run `make libs` to recompile only runtime libraries (`lib/`).


Tests
-----

Tests are divided into good (supposed to compile and run properly) and bad (should throw compilation errors).

There is a Python script `test.py`.
You can pass a path pattern to run only selected tests (e.g. `python test.py good`).
To see all options, run it with `-h`.

Tests serve currently also as a documentation of the language.
You can browse them to learn the syntax and semantics.


Final thoughts
--------------

The goal of this project is to create a language that would be simple, consistent, and powerful enough to be useful
for some basic tasks, where other languages are too verbose, unintuitive, error-prone, or not fast enough.
One example of a use-case could be solving algorithmic problems,
without constantly looking into C++ STL documentation or defining tons of macros.

I do know that there exist many interesting modern programming languages apart from those widely-known,
and most of them provide majority of features from my list. Even though I haven't used them,
I tried my best to learn about their details and discovered that none of them fully meets my expectations.
From what I've found, only Boo has an indentation-based syntax without braces, but is built on top of
C# and .NET platform. Other compiled languages with static typing and type inference are D, Go, Rust, Scala, and Kotlin,
but their syntax is uglier and they are either concentrated on some specific aspect like concurrency (the first 3),
or built on top of Java (the other 2).
