Pyxell
======

### Clear and easy to use multi-paradigm compiled programming language with static typing. ###


Motivation
----------

Do you like Python for its expressive and intuitive syntax, but miss static type checking and runtime speed of compiled languages?

Do you enjoy functional programming in Haskell, yet find it overly complicated and not exactly suitable for everyday use?

Do you keep looking back at C++ for its speed and power, though can't stand its verbosity and ugliness in comparison to modern languages?

That's why I started creating Pyxell - to bring together the best features of different programming languages.


Features
--------

This is a list of features planned for the 1.0 release. It will probably grow, maybe indefinitely :)

* Python-like syntax with semantic indentation (+)
* Strongly static typing with partial type inference (+)
* Full compilation to machine code (+)
* Native tuples (+)
* Immutable strings (+)
* Mutable arrays (+)
* First-class functions (+)
* Closures and lambdas
* Keyword arguments
* Arbitrary-precision arithmetic
* String interpolation
* Classes with multiple inheritance and safe references
* Separate nullable types
* Coroutines
* Module system
* Variety of containers: mutable/immutable, hash/tree-based
* List and dictionary comprehensions

These features would be also nice to have, but are more complicated and have less priority for me:

* Exceptions
* Automatic memory management
* Concurrency


Details
-------

* Type checker and LLVM compiler written in Haskell with BNFC.
* Compilation to machine code (and optimizations) with Clang.


Requirements
------------

These are the software versions that I use. Pyxell may work with others versions, but it is not guaranteed.

* GHC 8.2.2
* Cabal 2.0.0
* BNFC 2.8.1 with `176-source-position` branch 
* Clang 6.0.0 with C++ standard library
* Python 3.6.4 with `colorama` and `argparse` packages

For BNFC to store source code position, install it from source:

> git clone https://github.com/BNFC/bnfc.git \
> cd bnfc/source \
> git cherry-pick 1c88a2bfec200859e464db77dedfaf62c369394e \
> cabal install

Note: you might get compilation errors when using GHC 8.4 (https://github.com/BNFC/bnfc/pull/227).

To compile and link a Pyxell program correctly, a C++ standard library is required for Clang.
This shouldn't be a problem on Linux, but on Windows this may not work out of the box.
In some cases Windows SDK installation may be required
or it may be necessary to run `clang` with `-target x86_64-pc-windows-gnu` in `Main.hs`.


Usage
-----

> make \
> ./pyxell code.px

If the program is correct, `code.ll` file and an executable should be created in the same folder.
If not, errors will be displayed, pointing to the erroneous code location.


Tests
-----

Tests are divided into good (supposed to compile and run properly) and bad (should throw compilation errors).

There is a Python script `test.py`.
You can pass a path pattern to run only selected tests (e.g. `python test.py good` or `python test.py bad/arrays -e`).
To see all options, run it with `-h`.

Tests serve currently as documentation of the language.
You can browse them to learn the syntax and semantics (which are similar to Python's, though not exactly).


Final thoughts
--------------

Goal of this project is to create a language very simple and consistent and powerful enough to be useful
for some basic tasks, where other languages are too verbose, unintuitive, error-prone or not fast enough.
One example of such use-case could be solving algorithmic problems,
without constantly looking into C++ STL documentation or creating tons of macros.

I do know that there exist many interesting modern programming languages different from those widely-known,
and most of them provide majority of features from my list. Even though I haven't used them,
I've tried my best to learn about their details and discovered that none of them fully meets my expectations.

From what I've found, only Boo has a clear Python-inspired syntax without braces, but is built on top of
C# and .NET platform, which make it somewhat limited, even though I like C#.
Other compiled languages with static typing and type inference are D, Go, Rust, Scala, and Kotlin,
but their syntax is uglier and they are either concentrated on some specific aspect like concurrency (the first 3),
or built on top of Java (the other 2) which makes them even less interesting option for me.

Of course this is only my subjective point of view. I may be wrong about some of these languages
or I might have missed some cutting-edge features or maybe completely overlooked
some other great languages to compare - in such case, please let me know.

However, an important value of this project is also to learn new things, develop a language from scratch
and implement it in my own way, which certainly no other existing language is able to provide.
