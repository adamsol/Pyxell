
# Specification


## Operators

This table presents all operators available in Pyxell, sorted by precedence, from highest to lowest.
Operators in the same row have equal precedence.

| Operators                        | Description                                              | Arity     | Associativity |
| -------------------------------- | -------------------------------------------------------- | --------- | ------------- |
| `.`, `?.`                        | attribute access                                         | binary    | left          |
| `[]`, `?[]`                      | element access                                           | binary    | left          |
| `()`                             | function call                                            | multiary  | left          |
| `!`                              | non-null assertion                                       | unary     | left          |
| `^`, `^^`                        | exponentiation, integer exponentiation                   | binary    | right         |
| `+`, `-`                         | unary plus and minus                                     | unary     | right         |
| `/`                              | division                                                 | binary    | left          |
| `//`, `%`, `*`, `&`              | floor division, modulo, multiplication, set intersection | binary    | left          |
| `+`, `-`                         | addition, subtraction                                    | binary    | left          |
| `%%`                             | divisibility                                             | binary    | left          |
| `??`                             | null coalescing                                          | binary    | left          |
| `..`, `...`                      | inclusive and exclusive range                            | binary    | left          |
| `...`                            | infinite range                                           | unary     | left          |
| `by`                             | iteration step                                           | binary    | left          |
| `...`                            | spread                                                   | unary     | right         |
| `==`, `!=`, `<`, `<=`, `>`, `>=` | comparisons (chainable)                                  | binary    | right         |
| `in`, `not in`                   | membership                                               | binary    | left          |
| `is null`, `is not null`         | null check                                               | unary     | left          |
| `not`                            | logical negation                                         | binary    | right         |
| `and`                            | logical conjunction (short-circuiting)                   | binary    | right         |
| `or`                             | logical disjunction (short-circuiting)                   | binary    | right         |
| `? :`                            | conditional operator                                     | ternary   | right         |

Associativity of unary operators determines on which side the expression should be, e.g.: `a!` (left), `-a` (right).


## Types

This section describes all data types available in Pyxell, together with their properties and methods.

### Fundamental types

| Type name  | Description                                 | Example value | Default value |
| ---------- | ------------------------------------------- | ------------- | ------------- |
| `Void`     | no value (for functions returning nothing)  |               |               |
| `Int`      | 64-bit signed integer number                | `42`          | `0`           |
| `Rat`      | arbitrary-precision rational number         | `1.5`         | `0r`          |
| `Float`    | double-precision floating-point number      | `3.14f`       | `0f`          |
| `Bool`     | boolean value                               | `true`        | `false`       |
| `Char`     | single-byte character                       | `'A'`         | `'\x0'`       |
| `String`   | arbitrary-length string of characters       | `"example"`   | `""`          |

### Compound types

| Type name patterns                 | Description      | Example values     | Default value                            |
| ---------------------------------- | ---------------- | ------------------ | ---------------------------------------- |
| `[Type]`                           | array            | `[1, 2]`           | `[]`                                     |
| `{Type}`                           | set              | `{"abc", ""}`      | `{}`                                     |
| `{Key:Value}`                      | dictionary       | `{'x': false}`     | `{:}`                                    |
| `Type?`                            | nullable value   | `null`             | `null`                                   |
| `Type1*Type2`                      | tuple            | `true, 4.6`        | tuple of default values                  |
| `Type...`                          | generator object |                    | empty sequence                           |
| `Arg1->Arg2->Result`, `()->Result` | function         | `_+_`, `lambda: 0` | function returning the default value     |
| custom class name                  | class object     |                    | none (uninitialized object is invalid)   |

### `Int` properties

| Property name    | Type         | Description                                                      |
| ---------------- | ------------ | ---------------------------------------------------------------- |
| `char`           | `Char`       | character corresponding to the integer code (in ASCII)           |

### `Rat` properties and methods

| Property name    | Type         | Description                                                      |
| ---------------- | ------------ | ---------------------------------------------------------------- |
| `fraction`       | `Rat*Rat`    | numerator and denominator of the number, in the reduced form     |

| Method header                                     | Description                                                                                                     |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `toInt(): Int`                                    | returns the number converted to `Int` (conversion may be lossy)                                                 |

### `Float` methods

| Method header                                     | Description                                                                                                     |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `toInt(): Int`                                    | returns the number converted to `Int` (conversion may be lossy)                                                 |

### `Char` properties

| Property name    | Type         | Description                                                      |
| ---------------- | ------------ | ---------------------------------------------------------------- |
| `code`           | `Int`        | integer code of the character (in ASCII)                         |

### `String` properties and methods

| Property name    | Type         | Description                                                      |
| ---------------- | ------------ | ---------------------------------------------------------------- |
| `empty`          | `Bool`       | whether the string is empty                                      |
| `length`         | `Int`        | number of characters in the string                               |

| Method header                                     | Description                                                                                                     |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `all(f: Char->Bool): Bool`                        | determines whether all characters in the string satisfy a condition                                             |
| `any(f: Char->Bool): Bool`                        | determines whether any character in the string satisfies a condition                                            |
| `count(c: Char): Int`                             | returns the number of occurrences of a character within the string                                              |
| `endsWith(s: String): Bool`                       | determines whether the string ends with a given string                                                          |
| `filter(f: Char->Bool): String`                   | returns a string with only those characters from the original string that satisfy a condition                   |
| `find(s: String, start: Int = 0): Int?`           | returns the index of the first occurrence of a string within the string, or `null` if it is not found           |
| `fold<B>(f: Char->B->B, r: B): B`                 | applies an accumulator function over the string, with a given initial accumulator value                         |
| `get(p: Int): Char?`                              | returns the character under a given index in the string, or `null` if the index is out of bounds                |
| `map(f: Char->Char): String`                      | returns a string with characters from the original string transformed by a mapping function                     |
| `reduce(f: Char->Char->Char): Char`               | applies an accumulator function over the string, with the first character as the initial value                  |
| `split(sep: String): [String]`                    | splits the string into substrings delimited by a given separator                                                |
| `startsWith(s: String): Bool`                     | determines whether the string starts with a given string                                                        |
| `toInt(): Int`                                    | returns the string's content converted to `Int` (conversion may fail)                                           |
| `toFloat(): Float`                                | returns the string's content converted to `Float` (conversion may fail)                                         |
| `toRat(): Rat`                                    | returns the string's content converted to `Rat` (conversion may fail)                                           |

### Array properties and methods

| Property name    | Type         | Description                                                      |
| ---------------- | ------------ | ---------------------------------------------------------------- |
| `empty`          | `Bool`       | whether the array is empty                                       |
| `length`         | `Int`        | number of elements in the array                                  |

| Method header                                          | Description                                                                                                     |
| ------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| `all<A>(f: A->Bool = _): Bool`                         | determines whether all elements in the array satisfy a condition                                                |
| `any<A>(f: A->Bool = _): Bool`                         | determines whether any element in the array satisfies a condition                                               |
| `clear<A>(): Void`                                     | removes all elements from the array                                                                             |
| `copy<A>(): [A]`                                       | returns a shallow copy of the array                                                                             |
| `count<A>(x: A): Int`                                  | returns the number of occurrences of an element within the array                                                |
| `erase<A>(p: Int, count: Int = 1): Void`               | removes elements from the array at a given position                                                             |
| `extend<A>(a: [A]): Void`                              | appends all elements in a given array to the array                                                              |
| `filter<A>(f: A->Bool): [A]`                           | returns an array with only those elements from the original array that satisfy a condition                      |
| `find<A>(x: A, start: Int = 0): Int?`                  | returns the index of the first occurrence of an element within the array, or `null` if it is not found          |
| `fold<A,B>(f: A->B->B, r: B): B`                       | applies an accumulator function over the array, with a given initial accumulator value                          |
| `get<A>(p: Int): A?`                                   | returns the element under a given index in the array, or `null` if the index is out of bounds                   |
| `insert<A>(p: Int, x: A): Void`                        | inserts a new element at a given position of the array                                                          |
| `join<A>(sep: String = ""): String`                    | returns a string consisting of elements from the array (characters or strings) delimited by a given separator   |
| `map<A,B>(f: A->B): [B]`                               | returns an array with elements from the original array transformed by a mapping function                        |
| `pop<A>(): A`                                          | removes the last element from the array and returns it (will fail if the array is empty)                        |
| `push<A>(x: A): Void`                                  | appends a given element to the end of the array                                                                 |
| `reduce<A>(f: A->A->A): A`                             | applies an accumulator function over the array, with the first element as the initial value                     |
| `reverse<A>(): [A]`                                    | reverses the order of elements in the array in place, and returns the reversed array                            |
| `sort<A,K>(reverse: Bool = false, key: A->K = _): [A]` | sorts the array in place, stably, using a function to extract comparison keys, and returns the sorted array     |

### Set properties and methods

| Property name    | Type         | Description                                                      |
| ---------------- | ------------ | ---------------------------------------------------------------- |
| `empty`          | `Bool`       | whether the set is empty                                         |
| `length`         | `Int`        | number of elements in the set                                    |

| Method header                                     | Description                                                                                                     |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `add<A>(x: A): Void`                              | adds a given element to the set                                                                                 |
| `all<A>(f: A->Bool = _): Bool`                    | determines whether all elements in the set satisfy a condition                                                  |
| `any<A>(f: A->Bool = _): Bool`                    | determines whether any element in the set satisfies a condition                                                 |
| `clear<A>(): Void`                                | removes all elements from the set                                                                               |
| `copy<A>(): {A}`                                  | returns a shallow copy of the set                                                                               |
| `filter<A>(f: A->Bool): {A}`                      | returns a set with only those elements from the original set that satisfy a condition                           |
| `fold<A,B>(f: A->B->B, r: B): B`                  | applies an accumulator function over the set, with a given initial accumulator value                            |
| `intersect<A>(s: {A}): Void`                      | removes all elements not present in a given set from the set                                                    |
| `map<A,B>(f: A->B): {B}`                          | returns a set with elements from the original set transformed by a mapping function                             |
| `pop<A>(): A`                                     | removes the last element from the set and returns it (will fail if the set is empty)                            |
| `reduce<A>(f: A->A->A): A`                        | applies an accumulator function over the set, with one of the elements as the initial value                     |
| `remove<A>(x: A): Void`                           | removes a given element from the set                                                                            |
| `subtract<A>(s: {A}): Void`                       | removes all elements in a given set from the set                                                                |
| `union<A>(s: {A}): Void`                          | adds all elements in a given set to the set                                                                     |

### Dictionary properties and methods

| Property name    | Type         | Description                                                      |
| ---------------- | ------------ | ---------------------------------------------------------------- |
| `empty`          | `Bool`       | whether the dictionary is empty                                  |
| `length`         | `Int`        | number of elements in the dictionary                             |

| Method header                                     | Description                                                                                                     |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `all<A,B>(f: A*B->Bool): Bool`                    | determines whether all key-value pairs in the dictionary satisfy a condition                                    |
| `any<A,B>(f: A*B->Bool): Bool`                    | determines whether any key-value pair in the dictionary satisfies a condition                                   |
| `clear<A,B>(): Void`                              | removes all elements from the dictionary                                                                        |
| `copy<A,B>(): {A:B}`                              | returns a shallow copy of the dictionary                                                                        |
| `filter<A,B>(f: A*B->Bool): {A:B}`                | returns a dictionary with only those key-value pairs from the original dictionary that satisfy a condition      |
| `fold<A,B,C>(f: A*B->C->C, r: C): C`              | applies an accumulator function over the dictionary, with a given initial accumulator value                     |
| `get<A,B>(x: A): B?`                              | returns the value under a given key in the dictionary, or `null` if the key is not present                      |
| `map<A,B,C,D>(f: A*B->C*D): {C:D}`                | returns a dictionary with key-value pairs from the original dictionary transformed by a mapping function        |
| `pop<A,B>(): A*B`                                 | removes the last key-value pair from the dictionary and returns it (will fail if the dictionary is empty)       |
| `reduce<A,B>(f: A*B->A*B->A*B): A*B`              | applies an accumulator function over the dictionary, with one of the key-value pairs as the initial value       |
| `remove<A,B>(x: A): Void`                         | removes a given key from the dictionary                                                                         |
| `update<A,B>(d: {A:B}): Void`                     | updates the dictionary with keys and values from a given dictionary                                             |

### Tuple properties

| Property name    | Type         | Description                                                      |
| ---------------- | ------------ | ---------------------------------------------------------------- |
| letter `a`–`z`   | any          | corresponding element of the tuple                               |

### Generator methods

| Method header                                     | Description                                                                                                     |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `next<A>(): A`                                    | runs the generator and returns the yielded value                                                                |

### Common methods

| Method header                                     | Description                                                                                                     |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `toString(): String`                              | returns the string representation of the value                                                                  |


## Standard library

This section describes the built-in functions in Pyxell, as well as constants and functions within corresponding modules.

### I/O functions

| Function header                                   | Description                                                                                                     |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `read(): String`                                  | reads a string from the standard input, to the first whitespace character                                       |
| `readChar(): Char`                                | reads a single character from the standard input                                                                |
| `readFloat(): Float`                              | reads a floating-point number from the standard input                                                           |
| `readInt(): Int`                                  | reads an integer number from the standard input                                                                 |
| `readLine(): String`                              | reads a string from the standard input, to the first newline character                                          |
| `readRat(): Rat`                                  | reads a rational number from the standard input                                                                 |
| `write(s: String): Void`                          | writes a string to the standard output                                                                          |

### Bitwise functions

| Function header                                   | Description                                                                                                     |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `bitAnd(x: Int, y: Int): Int`                     | returns the bitwise AND of `x` and `y`                                                                          |
| `bitNot(x: Int): Int`                             | returns the bitwise NOT of `x`                                                                                  |
| `bitOr(x: Int, y: Int): Int`                      | returns the bitwise OR of `x` and `y`                                                                           |
| `bitShift(x: Int, y: Int): Int`                   | returns the bitwise shift of `x`: left for positive `y`, right for negative `y`                                 |
| `bitXor(x: Int, y: Int): Int`                     | returns the bitwise XOR of `x` and `y`                                                                          |

### Arithmetic functions

| Function header                                   | Description                                                                                                     |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `abs<T>(x: T): T`                                 | returns the absolute value of `x`                                                                               |
| `clamp<T>(x: T, a: T, b: T): T`                   | returns `x` clamped to the interval `[a, b]`                                                                    |
| `max<T>(x: T, y: T): T`                           | returns the maximum of `x` and `y`                                                                              |
| `min<T>(x: T, y: T): T`                           | returns the minimum of `x` and `y`                                                                              |
| `sign<T>(x: T): T`                                | returns the sign of `x` (`-1`, `0`, or `1`)                                                                     |

### `math` module

| Constant name    | Type         | Value                                                            |
| ---------------- | ------------ | ---------------------------------------------------------------- |
| E                | Float        | approximation of the number _e_: `2.718281828459045f`            |
| INF              | Float        | floating-point positive infinity                                 |
| PI               | Float        | approximation of the number _π_: `3.141592653589793f`            |

| Function header                                   | Description                                                                                                     |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `acos(x: Float): Float`                           | returns the angle (in radians) whose cosine is `x`                                                              |
| `asin(x: Float): Float`                           | returns the angle (in radians) whose sine is `x`                                                                |
| `atan(x: Float): Float`                           | returns the angle (in radians) whose tangent is `x`                                                             |
| `ceil(x: Float): Float`                           | returns the smallest integral value greater than or equal to `x`                                                |
| `cos(x: Float): Float`                            | returns the cosine of `x` (in radians)                                                                          |
| `exp(x: Float): Float`                            | returns _e_ raised to the power of `x`                                                                          |
| `floor(x: Float): Float`                          | returns the largest integral value less than or equal to `x`                                                    |
| `log(x: Float): Float`                            | returns the natural logarithm of `x`                                                                            |
| `log10(x: Float): Float`                          | returns the base 10 logarithm of `x`                                                                            |
| `round(x: Float, p: Int = 0): Float`              | returns `x` rounded to `p` fractional digits                                                                    |
| `sin(x: Float): Float`                            | returns the sine of `x` (in radians)                                                                            |
| `sqrt(x: Float): Float`                           | returns the square root of `x`                                                                                  |
| `tan(x: Float): Float`                            | returns the tangent of `x` (in radians)                                                                         |
| `trunc(x: Float): Float`                          | returns the integral part of `x` (`x` rounded towards 0)                                                        |

### `random` module

| Function header                                   | Description                                                                                                     |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `randFloat(r: Float = 1): Float`                  | returns a random floating-point number from the interval `[0, r)`                                               |
| `randInt(r: Int = 2): Float`                      | returns a random integer number from the interval `[0, r)`                                                      |
| `seed(x: Int): Float`                             | initializes the pseudo-random number generator with a given seed                                                |
