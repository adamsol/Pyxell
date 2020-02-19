
#define _CRT_SECURE_NO_WARNINGS

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <ctime>
#include <limits>
#include <functional>
#include <random>
#include <string>
#include <tuple>
#include <vector>

using namespace std::string_literals;

// https://github.com/godotengine/godot/pull/33376
#if defined(__MINGW32__) || (defined(_MSC_VER) && _MSC_VER < 1900 && defined(_TWO_DIGIT_EXPONENT)) && !defined(_UCRT)
	unsigned int old_exponent_format = _set_output_format(_TWO_DIGIT_EXPONENT);
#endif


/* Types */

using Void = void;
using Int = long long;
using Float = double;
using Char = char;
using Bool = bool;
using String = std::string;

template <typename T>
using Array = std::vector<T>;

template <typename... T>
using Tuple = std::tuple<T...>;


/* Arithmetic operators */

Int floordiv(Int a, Int b)
{
    if (b < 0) {
        return floordiv(-a, -b);
    }
    if (a < 0) {
        a -= b - 1;
    }
    return a / b;
}

Int mod(Int a, Int b)
{
    if (b < 0) {
        return -mod(-a, -b);
    }
    Int r = a % b;
    if (r < 0) {
        r += b;
    }
    return r;
}

Int pow(Int b, Int e)
{
    if (e < 0) {
        return 0;
    }
    Int r = 1;
    while (e > 0) {
        if (e % 2 != 0) {
            r *= b;
        }
        b *= b;
        e >>= 1;
    }
    return r;
}


/* String and array manipulation */

String asString(const Array<Char>& x)
{
    return String(x.begin(), x.end());
}

template <typename T>
T concat(T a, const T& b)
{
    a.insert(a.end(), b.begin(), b.end());
    return a;
}

template <typename T>
T multiply(const T& a, Int m)
{
    T r(a.size() * m, typename T::value_type());
    for (std::size_t i = 0; i < a.size(); ++i) {
        for (std::size_t j = 0; j < m; ++j) {
            r[j*a.size()+i] = a[i];
        }
    }
    return r;
}


/* Conversion to String */

char buffer[25];

String toString(Int x)
{
    sprintf(buffer, "%lld", x);
    return String(buffer);
}

String toString(Float x)
{
    sprintf(buffer, "%.15g", x);
    String r = String(buffer);
    if (std::all_of(r.begin(), r.end(), [](Char c) { return '0' <= c && c <= '9' || c == '-'; })) {
        r.append(".0");
    }
    return r;
}

String toString(Bool x)
{
    return x ? "true" : "false";
}

String toString(Char x)
{
    return String(1, x);
}

const String& toString(const String& x)
{
    return x;
}

template <typename T>
String toString(const Array<T>& x)
{
    String r;
    r.append("[");
    for (std::size_t i = 0; i < x.size(); ++i) {
        if (i > 0) {
            r.append(", ");
        }
        r.append(toString(x[i]));
    }
    r.append("]");
    return r;
}

template <std::size_t I = 0, typename... T>
String toString(const Tuple<T...>& x)
{
    // https://stackoverflow.com/a/54225452/12643160
    String r;
    r.append(toString(std::get<I>(x)));
    if constexpr(I+1 < sizeof...(T)) {
        r.append(" ");
        r.append(toString<I+1>(x));
    }
    return r;
}


/* Conversion to Int */

Int toInt(Int x)
{
    return x;
}

Int toInt(Float x)
{
    return static_cast<Int>(x);
}

Int toInt(Bool x)
{
    return x ? 1 : 0;
}

Int toInt(const String& x)
{
    Int r;
    sscanf(x.c_str(), "%lld", &r);
    return r;
}

Int toInt(Char x)
{
    return toInt(toString(x));
}


/* Conversion to Float */

Float toFloat(Int x)
{
    return static_cast<Float>(x);
}

Float toFloat(Float x)
{
    return x;
}

Float toFloat(Bool x)
{
    return x ? 1.0 : 0.0;
}

Float toFloat(const String& x)
{
    Float r;
    sscanf(x.c_str(), "%lg", &r);
    return r;
}

Float toFloat(Char x)
{
    return toFloat(toString(x));
}


/* Standard output */

template <typename T>
void write(const T& x)
{
    printf("%s", toString(x).c_str());
}


/* Standard input */

char input[1024];

String read()
{
    scanf("%1023s", input);
    return String(input);
}

String readLine()
{
    scanf("%1023[^\n]%*c", input);
    return String(input);
}

Int readInt()
{
    Int r;
    scanf("%lld", &r);
    return r;
}

Float readFloat()
{
    Float r;
    scanf("%lg", &r);
    return r;
}

Char readChar()
{
    Char r;
    scanf("%c", &r);
    return r;
}


/* Random numbers */

std::mt19937_64 generator(time(nullptr));

void seed(Int x)
{
    generator.seed(x);
}

Int _rand()
{
    return generator() & std::numeric_limits<Int>::max();
}

Int randInt(Int r)
{
    return _rand() % r;
}

Float randFloat(Float r)
{
    return _rand() * r / std::numeric_limits<Int>::max();
}
