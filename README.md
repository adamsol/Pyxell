Pyxell
======

### Clear and easy-to-use multi-paradigm compiled programming language with static typing. ###

*Note: Up to version 0.6.0 the project had been developed in Haskell with BNFC. Now it has been rewritten to Python and ANTLR.*


Motivation
----------

The project aims to combine the best features of different programming languages,
pack them into a clean syntax with significant indentation,
and provide the execution speed of native machine code.

It draws mainly from Python, Haskell, C#, and C++,
and tries to avoid common design flaws that have been nicely described
[in this blog post](https://eev.ee/blog/2016/12/01/lets-stop-copying-c/).


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
func reduce<A,B>([A] a, A->B->B f, B r) B def
    for x in a do
        r = f(x, r)
    return r

print reduce(_*_, 1, [2, 3, 4])  -- 24
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
* Generic functions (+)
* Module system (+/-)
* Classes with safe references (+)
* Separate nullable types (+)

To do:

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

* LLVM IR generator and type checker written in Python with ANTLR and llvmlite.
* Compilation to machine code (and optimizations) with Clang.


Requirements
------------

* Python 3.8 with packages from `requirements.txt`.

Sometimes installation of `llvmlite` [fails](https://github.com/numba/llvmlite/issues/527).
If such a problem occurs, try using `easy_install` instead of `pip install`.

* Clang 6 with C++ standard library.

The library shouldn't be a problem on Linux, but on Windows this may not work out of the box.
In some cases Windows SDK installation may be required
or it may be necessary to run `pyxell` with `-target x86_64-pc-windows-gnu`
(run `test.py` with `-t` argument to use this).

* ANTLR 4.7.2 (to build the parser).

Put `antlr-4.7.2-complete.jar` file into `src` folder.


Usage
-----

```
. pyxell.sh program.px
```

If the program is correct, `program.ll` file and an executable should be created in the same folder.
If not, errors will be displayed, pointing to the erroneous code location.

Run `make` after changing the grammar (`src/Pyxell.g4`) to rebuild the parser with ANTLR.


Tests
-----

```
python test.py -v
```

Tests are divided into good (supposed to compile and run properly) and bad (should throw compilation errors).

The script is multi-threaded.
Total execution time may vary from something like 10 seconds to 2 minutes,
depending on the number of processors in your machine and other factors.

You can pass a path pattern to run only selected tests (e.g. `python test.py arrays`).
To see all options, run it with `-h`.

Tests serve currently also as a documentation of the language.
You can browse them to learn the syntax and semantics.


Alternatives
------------

There are only a few languages with indentation-based syntax.
Some more or less similar to Pyxell are, in alphabetical order:
* [Boo](https://boo-language.github.io/) (based on .NET),
* [CoffeeScript](https://coffeescript.org/) (transpiled to JS),
* [F#](https://fsharp.org/) (functional, based on .NET),
* [Genie](https://wiki.gnome.org/Projects/Genie) (compiled via C),
* [Haskell](https://www.haskell.org/) (functional, compiled),
* [Nim](https://nim-lang.org/) (compiled via C/C++ or transpiled to JS),
* [Python](https://www.python.org/) (dynamically typed).
