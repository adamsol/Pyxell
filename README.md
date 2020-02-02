Pyxell
======

### Clean and easy-to-use multi-paradigm programming language with static typing, compiled to C++. ###


Motivation
----------

The project aims to combine the best features of different programming languages,
pack them into a clean and consistent syntax,
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
a = ['A'..'Z']
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

* Compilation to machine code via C++ (+)
* Python-like syntax with semantic indentation (+)
* Strongly static typing with partial type inference (+)
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


Requirements
------------

* Python 3.6+ with packages from `requirements.txt`.

```
python -m pip install -r requirements.txt
```

* C++17 compiler (e.g. GCC 7+ or Clang 5+) to build executables.


Usage
-----

```
python pyxell.py [-r] program.px
```

If the program is correct, `program.cpp` file and `program.exe` executable will be created in the same folder.
If not, errors will be displayed, pointing to the erroneous code location.

If `-r` option is given, the compiled program will be run immediately after compilation.

By default, `g++` command is used to compile the code.
You can pick a different command using `-c` option.
Write `-c=none` to skip the compilation step (only C++ code will be created).


Executable
----------

You can build a standalone application using `pyinstaller`. Install it using `pip`, then run `make exe`.
An executable `pyxell.exe` (not requiring Python to run) will be created in the `dist/pyxell` folder.


Development
-----------

In order to rebuild the parser from the grammar (`src/Pyxell.g4`),
first [download ANTLR](https://www.antlr.org/download/antlr-4.7.2-complete.jar)
and put the `antlr-4.7.2-complete.jar` file into `src` folder,
then run `make parser`.

After changing the code of Pyxell libraries (`lib/*.px` files),
run `make libs` to rebuild them.


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


History
-------

* The project was originaly written in Haskell, with BNFC as the parser generator, and used LLVM as the target language.
* In version 0.7.0 the code was rewritten to Python and used ANTLR as the parser generator.
* In version 0.9.0 the project was refactored to use C++ as the target language.
