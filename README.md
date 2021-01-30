Pyxell
======

### Clean and easy-to-use multi-paradigm programming language with static typing. ###


Documentation
-------------

https://www.pyxell.org/docs/

**[Examples](https://www.pyxell.org/docs/manual.html#examples)** | **[Playground](https://www.pyxell.org/docs/playground.html)**


Motivation
----------

Pyxell [_pixel_] aims to combine the best features of different programming languages,
pack them into a clean and consistent syntax,
and provide the execution speed of native machine code.

It draws mainly from Python, C++, C#, and Haskell,
trying to avoid common design flaws that have been nicely described
[in this blog post](https://eev.ee/blog/2016/12/01/lets-stop-copying-c/).


Features
--------

* Python-like syntax with semantic indentation
* Strongly static typing with partial type inference
* 64-bit integers and double-precision floating-point numbers
* Arbitrary-precision rational numbers
* Immutable strings
* String interpolation
* Mutable containers: array, set, dictionary
* Array/string slicing
* Complex for-loops with ranges, steps, and zipping
* Array/set/dictionary comprehension
* Native tuples
* First-class functions
* Default, named, and variadic function arguments
* Lambda expressions
* Generic functions
* Generators
* Classes with safe references
* Inheritance and virtual methods
* Nullable types
* Full transpilation to C++ and compilation to machine code
* Automatic memory management (utilizing C++'s smart pointers)

To do:

* Exception handling
* Static class fields and methods
* Complex numbers
* Unicode support
* Module system
* Multiple inheritance
* Generic classes
* Operator overloading
* Asynchronous programming


Requirements
------------

* Python 3.6+ with packages from `requirements.txt`.

```
python -m pip install -r requirements.txt
```

* C++17 compiler: Clang 5+ or GCC 7+.

Note that generators are currently available only with Clang, since they are based on C++'s coroutines.
Though GCC 10 also supports coroutines, as of version 10.2 the implementation is buggy
(see [here](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=95591) or [here](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=95823)),
so it is not yet supported by Pyxell.


Usage
-----

```
python pyxell.py program.px
```

If the program is valid, `program.cpp` file and `program.exe` executable will be created in the same folder,
and it will be automatically executed (unless you add `-n` option).
Otherwise, errors will be displayed, pointing to the erroneous code location.

By default, `clang` command is used to compile the code.
You can pick a different compiler using `-c` option.

The executable is not optimized by default.
You can set the optimization level with `-O` option, e.g. `-O2`.
This will make the program run faster, but also make the compilation slower.

Use `-s` to skip the compilation step and obtain transpiled C++ code with all headers included,
ready for manual compilation (with `-std=c++17` option, and with `-fcoroutines-ts` in the case of Clang).

To see all options, use `-h`.


PyInstaller
-----------

You can build a standalone compiler application using `PyInstaller`.
Install `PyInstaller` with `pip`, then run `make exe`.
An executable (not requiring Python to run) will be created in the `dist/pyxell` folder.


Development
-----------

In order to rebuild the parser from the grammar (`src/Pyxell.g4`),
first [download ANTLR](https://www.antlr.org/download/antlr-4.9.1-complete.jar)
and put the `antlr*.jar` file into `src` folder,
then run `make parser`.

After changing the code of Pyxell libraries (`lib/*.px` files),
run `make libs` to rebuild them.

To build the documentation, go to the `docs` folder, run `npm install`, then `make`.
To start a documentation server locally, install `flask` and run `server.py` in the same folder.


Tests
-----

```
python test.py
```

Tests are divided into good (supposed to compile and run properly) and bad (should throw compilation errors).

By default, the whole C++ code for valid tests is merged, so that only one file is compiled,
which is faster than compiling hundreds of files individually, even using multiple threads.
Total execution time (with default settings) should be around 30-60 seconds.

If, however, the script fails with an error like this: `too many sections` / `file too big`
(seen with GCC 7.2 on Windows), or there is another compilation error that is hard to decipher,
then you might need to add the `-s` option so that each test is compiled separately.

You can pass a path pattern to run only selected tests (e.g. `python test.py arrays`).

To see all options, run the script with `-h`.


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
* In version 0.7.0 the code was rewritten to Python, with ANTLR as the parser generator.
* In version 0.9.0 the project was refactored to use C++ as the target language.
