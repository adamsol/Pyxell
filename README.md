Pyxell
======

### Clean and easy-to-use multi-paradigm programming language with static typing. ###


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

Rational numbers:

```
print 1/10 + 5^-1  -- 3/10
```

Range literals, string interpolation:

```
a = ['A'..'Z']
for x, i in a, 0... step 5 do
    print "a[{i}] = {x}" 
```

Dynamic containers:

```
[Int] a = [1]  -- array (Python's list / C++'s vector)
a.push(2)

{Float} b = {3.0}  -- hash set
b.add(4.0)

{Char:String} c = {'5': "6"}  -- dictionary (hash map) 
c['7'] = "8"
```

Functions, tuples:

```
func fib(Int n) Int def
    if n <= 0 do
        return 0
    a, b = 0, 1
    for i in 2..n do
        a, b = b, a+b
    return b
        
print fib(10)
```

Generic functions, lambda expressions:

```
func fold<A,B>([A] a, A->B->B f, B r) B def
    for x in a do
        r = f(x, r)
    return r

print fold([2, 3, 4], _*_, 1)  -- 24

-- There are built-in methods like this:
print [0..10 step 2].reduce(_+_)  -- 30
```

Classes, nullable types:

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
* Default and named function arguments
* Lambda expressions
* Generic functions
* Classes with safe references
* Inheritance and virtual methods
* Nullable types
* Full transpilation to C++17 and compilation to machine code
* Automatic memory management (utilizing C++'s smart pointers)

To do:

* Closures
* Coroutines/generators
* Exception handling
* Unicode
* Generic classes
* Operator overloading
* Multiple inheritance
* Concurrency
* Module system


Requirements
------------

* Python 3.6+ with packages from `requirements.txt`.

```
python -m pip install -r requirements.txt
```

* C++17 compiler (e.g. GCC 7+ or Clang 5+).


Usage
-----

```
python pyxell.py [-r] program.px
```

If the program is correct, `program.cpp` file and `program.exe` executable will be created in the same folder.
If not, errors will be displayed, pointing to the erroneous code location.

If `-r` option is given, the compiled program will be run immediately after compilation.

By default, `gcc` command is used to compile the code.
You can pick a different command using `-c` option.
Write `-c=none` to skip the compilation step (only C++ code will be created).


PyInstaller
-----------

You can build a standalone application using `PyInstaller`. Install it using `pip`, then run `make exe`.
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
python test.py --verbose --fast
```

Tests are divided into good (supposed to compile and run properly) and bad (should throw compilation errors).

The script is multi-threaded and uses Clang as the default C++ compiler (contrary to standard compilation, where GCC is the default).
Total execution time should be around 30 seconds.

If, however, the tests fail with an error like this: `too many sections` / `file too big` (seen with GCC 7.2 on Windows),
then you might need to drop the `--fast` option, which will increase the execution time significantly.

You can pass a path pattern to run only selected tests (e.g. `python test.py arrays`).

To see all options, run the script with `-h`.

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
* In version 0.7.0 the code was rewritten to Python, with ANTLR as the parser generator.
* In version 0.9.0 the project was refactored to use C++ as the target language.
