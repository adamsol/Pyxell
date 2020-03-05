
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
#include <unordered_set>
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

using Unknown = void*;

using Void = void;
using Int = long long;
using Float = double;
using Char = char;
using Bool = bool;

/* String */

using String = ptr<std::string>;

template <typename... Args>
String make_string(Args&&... args)
{
    return String(std::make_shared<std::string>(std::forward<Args>(args)...));
}

/* Array */

template <typename T>
struct Array: public ptr<std::vector<T>>
{
    using ptr<std::vector<T>>::ptr;

    Array(const Array<Unknown>& x)
    {
        this->p = std::make_shared<std::vector<T>>();
    }

    template <typename U>
    Array(const Array<U>& x)
    {
        this->p = std::make_shared<std::vector<T>>(x->begin(), x->end());
    }
};

template <typename T>
Array<T> make_array(std::initializer_list<T> x)
{
    return Array<T>(std::make_shared<std::vector<T>>(x));
}

template <typename T, typename... Args>
Array<T> make_array(Args&&... args)
{
    return Array<T>(std::make_shared<std::vector<T>>(std::forward<Args>(args)...));
}

/* Set */

template <typename T>
struct Set: public ptr<std::unordered_set<T>>
{
    using ptr<std::unordered_set<T>>::ptr;

    Set(const Set<Unknown>& x)
    {
        this->p = std::make_shared<std::unordered_set<T>>();
    }

    template <typename U>
    Set(const Set<U>& x)
    {
        this->p = std::make_shared<std::unordered_set<T>>(x->begin(), x->end());
    }
};

template <typename T>
Set<T> make_set(std::initializer_list<T> x)
{
    return Set<T>(std::make_shared<std::unordered_set<T>>(x));
}

template <typename T, typename... Args>
Set<T> make_set(Args&&... args)
{
    return Set<T>(std::make_shared<std::unordered_set<T>>(std::forward<Args>(args)...));
}

/* Nullable */

template <typename T>
struct Nullable: public std::optional<T>
{
    using std::optional<T>::optional;
    operator bool() = delete;

    Nullable(const Nullable<Unknown>& x): std::optional<T>() {}
};

/* Tuple */

template <typename... T>
using Tuple = std::tuple<T...>;

/* Class */

template <typename... T>
using Object = std::shared_ptr<T...>;


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


/* Operators for strings and arrays */

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
Array<T> concat(const Array<T>& a, const Array<T>& b)
{
    auto r = make_array<T>({});
    r->insert(r->end(), a->begin(), a->end());
    r->insert(r->end(), b->begin(), b->end());
    return r;
}

template <typename T>
T multiply(const T& v, Int m)
{
    auto r = T(v.size()*m, typename T::value_type());

    for (std::size_t i = 0; i < v.size(); ++i) {
        for (std::size_t j = 0; j < m; ++j) {
            r[j*v.size()+i] = v[i];
        }
    }
    return r;
}

String multiply(const String& x, Int m)
{
    return make_string(multiply(*x, m));
}

template <typename T>
Array<T> multiply(const Array<T>& x, Int m)
{
    return make_array<T>(multiply(*x, m));
}

template <typename T>
T slice(const T& v, const Nullable<Int>& a, const Nullable<Int>& b, Int step)
{
    Int length = v.size();

    Int start;
    if (a.has_value()) {
        start = a.value();
        if (start < 0) {
            start += length;
        }
    } else {
        start = step > 0 ? 0LL : length;
    }
    start = std::clamp(start, 0LL, length);

    Int end;
    if (b.has_value()) {
        end = b.value();
        if (end < 0) {
            end += length;
        }
    } else {
        end = step > 0 ? length : 0LL;
    }
    end = std::clamp(end, 0LL, length);

    auto r = T();

    if (step < 0) {
        for (Int i = start; i > end; i += step) {
            r.push_back(v[i-1]);
        }
    } else {
        for (Int i = start; i < end; i += step) {
            r.push_back(v[i]);
        }
    }
    return r;
}

String slice(const String& x, const Nullable<Int>& a, const Nullable<Int>& b, Int c)
{
    return make_string(slice(*x, a, b, c));
}

template <typename T>
Array<T> slice(const Array<T>& x, const Nullable<Int>& a, const Nullable<Int>& b, Int c)
{
    return make_array<T>(slice(*x, a, b, c));
}


/* Array methods */

template <typename T>
Void push(const Array<T>& x, const T& e)
{
    x->push_back(e);
}

template <typename T>
Void insert(const Array<T>& x, Int p, const T& e)
{
    if (p < 0) {
        p += x->size();
    }
    x->insert(x->begin()+p, e);
}

template <typename T>
Void extend(const Array<T>& x, const Array<T>& y)
{
    x->reserve(x->size() + y->size());
    x->insert(x->end(), y->begin(), y->end());
}

template <typename T>
T pop(const Array<T>& x)
{
    auto r = x->back();
    x->pop_back();
    return r;
}

template <typename T>
Void erase(const Array<T>& x, Int p, Int n)
{
    if (p < 0) {
        p += x->size();
    }
    x->erase(x->begin()+p, x->begin()+p+n);
}

template <typename T>
Void clear(const Array<T>& x)
{
    x->clear();
}

template <typename T>
Void reverse(const Array<T>& x)
{
    std::reverse(x->begin(), x->end());
}

template <typename T>
Array<T> copy(const Array<T>& x)
{
    return make_array<T>(*x);
}

template <typename T>
Nullable<Int> find(const Array<T>& x, const T& e)
{
    for (std::size_t i = 0; i < x->size(); ++i) {
        if ((*x)[i] == e) {
            return Nullable<Int>(i);
        }
    }
    return Nullable<Int>();
}

template <typename T>
Int count(const Array<T>& x, const T& e)
{
    return std::count(x->begin(), x->end(), e);
}


/* Conversion to String */

char buffer[25];

template <typename T> String toString(const Nullable<T>& x);
template <std::size_t I = 0, typename... T> String toString(const Tuple<T...>& x);

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
String toString(const Set<T>& x)
{
    auto r = make_string();
    r->append("{");
    for (auto it = x->begin(); it != x->end(); ++it) {
        if (it != x->begin()) {
            r->append(", ");
        }
        r->append(*toString(*it));
    }
    r->append("}");
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

template <std::size_t I, typename... T>
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

template <typename T>
String toString(const Object<T>& x)
{
    return reinterpret_cast<String (*)(Object<T>)>(x->toString())(x);
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
