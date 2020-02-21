
#define _CRT_SECURE_NO_WARNINGS

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <ctime>
#include <limits>
#include <functional>
#include <memory>
#include <optional>
#include <random>
#include <string>
#include <tuple>
#include <vector>

// https://github.com/godotengine/godot/pull/33376
#if defined(__MINGW32__) || (defined(_MSC_VER) && _MSC_VER < 1900 && defined(_TWO_DIGIT_EXPONENT)) && !defined(_UCRT)
	unsigned int old_exponent_format = _set_output_format(_TWO_DIGIT_EXPONENT);
#endif


/* Wrapper around shared_ptr for proper comparison operators */

template <typename T>
struct ptr
{
    std::shared_ptr<T> p;

    ptr() {}
    ptr(std::shared_ptr<T> p): p(p) {}

    T& operator *() const { return *p; }
    T* operator ->() const { return p.get(); }
};

template <typename T> bool operator ==(const ptr<T>& lhs, const ptr<T>& rhs) { return *lhs == *rhs; }
template <typename T> bool operator !=(const ptr<T>& lhs, const ptr<T>& rhs) { return *lhs != *rhs; }
template <typename T> bool operator <(const ptr<T>& lhs, const ptr<T>& rhs) { return *lhs < *rhs; }
template <typename T> bool operator >(const ptr<T>& lhs, const ptr<T>& rhs) { return *lhs > *rhs; }
template <typename T> bool operator <=(const ptr<T>& lhs, const ptr<T>& rhs) { return *lhs <= *rhs; }
template <typename T> bool operator >=(const ptr<T>& lhs, const ptr<T>& rhs) { return *lhs >= *rhs; }


/* Types */

using Void = void;
using Int = long long;
using Float = double;
using Char = char;
using Bool = bool;

using String = ptr<std::string>;

template <typename... Args>
String make_string(Args&&... args)
{
    return String(std::make_shared<std::string>(std::forward<Args>(args)...));
}

template <typename T>
using Array = ptr<std::vector<T>>;

template <typename T>
Array<T> make_array(std::initializer_list<T> x)
{
    return Array<T>(std::make_shared<std::vector<T>>(x));
}

template <typename... T>
using Tuple = std::tuple<T...>;

template <typename T>
using Nullable = std::optional<T>;


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
    return make_string(x->begin(), x->end());
}

String concat(const String& a, const String& b)
{
    return make_string(*a + *b);
}

String concat(const String& a, Char b)
{
    return make_string(*a + b);
}

String concat(Char a, const String& b)
{
    return make_string(a + *b);
}

template <typename T>
ptr<T> concat(const ptr<T>& a, const ptr<T>& b)
{
    auto r = ptr<T>(std::make_shared<T>(*a));
    r->insert(r->end(), b->begin(), b->end());
    return r;
}

template <typename T>
ptr<T> multiply(const ptr<T>& a, Int m)
{
    auto r = ptr<T>(std::make_shared<T>(a->size() * m, typename T::value_type()));
    for (std::size_t i = 0; i < a->size(); ++i) {
        for (std::size_t j = 0; j < m; ++j) {
            (*r)[j*a->size()+i] = (*a)[i];
        }
    }
    return r;
}


/* Conversion to String */

char buffer[25];

String toString(Int x)
{
    sprintf(buffer, "%lld", x);
    return make_string(buffer);
}

String toString(Float x)
{
    sprintf(buffer, "%.15g", x);
    auto r = make_string(buffer);
    if (std::all_of(r->begin(), r->end(), [](Char c) { return ('0' <= c && c <= '9') || c == '-'; })) {
        r->append(".0");
    }
    return r;
}

String toString(Bool x)
{
    return make_string(x ? "true" : "false");
}

String toString(Char x)
{
    return make_string(1, x);
}

String toString(const String& x)
{
    return x;
}

template <typename T>
String toString(const Array<T>& x)
{
    auto r = make_string();
    r->append("[");
    for (std::size_t i = 0; i < x->size(); ++i) {
        if (i > 0) {
            r->append(", ");
        }
        r->append(*toString((*x)[i]));
    }
    r->append("]");
    return r;
}

template <typename T>
String toString(const Nullable<T>& x)
{
    if (x.has_value()) {
        return toString(x.value());
    } else {
        return make_string("null");
    }
}

template <std::size_t I = 0, typename... T>
String toString(const Tuple<T...>& x)
{
    // https://stackoverflow.com/a/54225452/12643160
    auto r = make_string();
    r->append(*toString(std::get<I>(x)));
    if constexpr(I+1 < sizeof...(T)) {
        r->append(" ");
        r->append(*toString<I+1>(x));
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
    sscanf(x->c_str(), "%lld", &r);
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
    sscanf(x->c_str(), "%lg", &r);
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
    printf("%s", toString(x)->c_str());
}


/* Standard input */

char input[1024];

String read()
{
    scanf("%1023s", input);
    return make_string(input);
}

String readLine()
{
    scanf("%1023[^\n]%*c", input);
    return make_string(input);
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
