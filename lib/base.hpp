
#define _CRT_SECURE_NO_WARNINGS

#include <algorithm>
#include <cctype>
#include <cmath>
#include <cstdio>
#include <ctime>
#include <limits>
#include <functional>
#include <iostream>
#include <iterator>
#include <memory>
#include <optional>
#include <random>
#include <string>
#include <tuple>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

#include "indy256/bigint.hpp"

#ifdef __clang__
    #include "cppcoro/generator.hpp"
#endif

using namespace std::literals::string_literals;


// https://github.com/godotengine/godot/pull/33376
#if defined(__MINGW32__) || (defined(_MSC_VER) && _MSC_VER < 1900 && defined(_TWO_DIGIT_EXPONENT)) && !defined(_UCRT)
    unsigned int old_exponent_format = _set_output_format(_TWO_DIGIT_EXPONENT);
#endif


template <typename T, typename U>
void safe_advance(T& it, const U& end, std::size_t n)
{
    for (std::size_t i = 0; i < n && it != end; ++i, ++it);
}


/* Types */

using Unknown = void*;

using Void = void;
using Int = long long;
using Float = double;
using Char = char;
using Bool = bool;

/* Rational */

struct Rat
{
    bigint numerator, denominator;

    Rat(): denominator(1) {}
    Rat(long long n): numerator(n), denominator(1) {}

    Rat(const std::string& s): denominator(1)
    {
        std::size_t p = s.find('/');
        numerator = bigint(s.substr(0, p));
        if (p != s.npos) {
            denominator = bigint(s.substr(p+1));
        }
        reduce();
    }

    void reduce()
    {
        bigint d = gcd(numerator, denominator);
        numerator /= d;
        denominator /= d;

        numerator.sign *= denominator.sign;
        denominator.sign = 1;
    }

    Rat& operator *= (const Rat& other)
    {
        numerator *= other.numerator;
        denominator *= other.denominator;
        reduce();
        return *this;
    }
    Rat& operator /= (const Rat& other)
    {
        numerator *= other.denominator;
        denominator *= other.numerator;
        reduce();
        return *this;
    }
    Rat& operator %= (const Rat& other)
    {
        numerator = (numerator * other.denominator) % (other.numerator * denominator);
        denominator *= other.denominator;
        reduce();
        return *this;
    }
    Rat& operator += (const Rat& other)
    {
        numerator *= other.denominator;
        numerator += denominator * other.numerator;
        denominator *= other.denominator;
        reduce();
        return *this;
    }
    Rat& operator -= (const Rat& other)
    {
        numerator *= other.denominator;
        numerator -= denominator * other.numerator;
        denominator *= other.denominator;
        reduce();
        return *this;
    }

    operator double () const
    {
        return numerator.doubleValue() / denominator.doubleValue();
    }

    bool operator == (const Rat& other) const { return numerator == other.numerator && denominator == other.denominator; }
    bool operator != (const Rat& other) const { return numerator != other.numerator || denominator != other.denominator; }
    bool operator < (const Rat& other) const { return numerator * other.denominator < denominator * other.numerator; }
    bool operator > (const Rat& other) const { return numerator * other.denominator > denominator * other.numerator; }
    bool operator <= (const Rat& other) const { return numerator * other.denominator <= denominator * other.numerator; }
    bool operator >= (const Rat& other) const { return numerator * other.denominator >= denominator * other.numerator; }
};

Rat operator * (Rat a, const Rat& b)
{
    return a *= b;
}
Rat operator / (Rat a, const Rat& b)
{
    return a /= b;
}
Rat operator % (Rat a, const Rat& b)
{
    return a %= b;
}
Rat operator + (Rat a, const Rat& b)
{
    return a += b;
}
Rat operator - (Rat a, const Rat& b)
{
    return a -= b;
}
Rat operator - (Rat a)
{
    a.numerator.sign = -a.numerator.sign;
    return a;
}

namespace std
{
    template <>
    struct hash<Rat>
    {
        size_t operator () (const Rat& x) const
        {
            std::size_t seed = 0;
            for (int e: x.numerator.z) {
                seed ^= hash<int>()(e) + 0x9e3779b9 + (seed << 6) + (seed >> 2);
            }
            for (int e: x.denominator.z) {
                seed ^= hash<int>()(e) + 0x9e3779b9 + (seed << 6) + (seed >> 2);
            }
            return seed;
        }
    };
}

/* Wrapper around shared_ptr for proper comparison operators and hash function */

template <typename T>
struct custom_ptr
{
    std::shared_ptr<T> p;

    custom_ptr() {}
    custom_ptr(std::shared_ptr<T> p): p(p) {}

    T& operator * () const { return *p; }
    T* operator -> () const { return p.get(); }
};

template <typename T> bool operator == (const custom_ptr<T>& lhs, const custom_ptr<T>& rhs) { return *lhs == *rhs; }
template <typename T> bool operator != (const custom_ptr<T>& lhs, const custom_ptr<T>& rhs) { return *lhs != *rhs; }
template <typename T> bool operator < (const custom_ptr<T>& lhs, const custom_ptr<T>& rhs) { return *lhs < *rhs; }
template <typename T> bool operator > (const custom_ptr<T>& lhs, const custom_ptr<T>& rhs) { return *lhs > *rhs; }
template <typename T> bool operator <= (const custom_ptr<T>& lhs, const custom_ptr<T>& rhs) { return *lhs <= *rhs; }
template <typename T> bool operator >= (const custom_ptr<T>& lhs, const custom_ptr<T>& rhs) { return *lhs >= *rhs; }

/* String */

struct String: public custom_ptr<std::string>
{
    using custom_ptr<std::string>::custom_ptr;

    String(Char x)
    {
        this->p = std::make_shared<std::string>(1, x);
    }
};

template <typename... Args>
String make_string(Args&&... args)
{
    return String(std::make_shared<std::string>(std::forward<Args>(args)...));
}

namespace std
{
    template <>
    struct hash<String>
    {
        size_t operator () (const String& x) const
        {
            return hash<std::string>()(*x);
        }
    };
}

/* Array */

template <typename T>
struct Array: public custom_ptr<std::vector<T>>
{
    using custom_ptr<std::vector<T>>::custom_ptr;

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
struct Set: public custom_ptr<std::unordered_set<T>>
{
    using custom_ptr<std::unordered_set<T>>::custom_ptr;

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

/* Dict */

template <typename K, typename V>
struct Dict: public custom_ptr<std::unordered_map<K, V>>
{
    using custom_ptr<std::unordered_map<K, V>>::custom_ptr;

    Dict(const Dict<Unknown, Unknown>& x)
    {
        this->p = std::make_shared<std::unordered_map<K, V>>();
    }

    template <typename L, typename W>
    Dict(const Dict<L, W>& x)
    {
        this->p = std::make_shared<std::unordered_map<K, V>>(x->begin(), x->end());
    }
};

template <typename K, typename V>
Dict<K, V> make_dict(std::initializer_list<std::pair<const K, V>> x)
{
    auto r = Dict<K, V>(std::make_shared<std::unordered_map<K, V>>());
    for (auto&& p: x) {
        r->insert_or_assign(p.first, p.second);
    }
    return r;
}

template <typename K, typename V, typename... Args>
Dict<K, V> make_dict(Args&&... args)
{
    return Dict<K, V>(std::make_shared<std::unordered_map<K, V>>(std::forward<Args>(args)...));
}

/* Nullable */

template <typename T>
struct Nullable: public std::optional<T>
{
    using std::optional<T>::optional;
    operator bool () = delete;  // so that null isn't displayed as false

    Nullable(const Nullable<Unknown>& x): std::optional<T>() {}
};

template <typename T>
bool operator == (const Nullable<T>& lhs, const Nullable<T>& rhs)
{
    return static_cast<std::optional<T>>(lhs) == static_cast<std::optional<T>>(rhs);
}

template <typename T>
struct std::hash<Nullable<T>>
{
    std::size_t operator () (const Nullable<T>& x) const
    {
        return hash<std::optional<T>>()(x);
    }
};

/* Tuple */

template <typename... T>
using Tuple = std::tuple<T...>;

// https://www.variadic.xyz/2018/01/15/hashing-stdpair-and-stdtuple/
// https://stackoverflow.com/a/15124153
// https://stackoverflow.com/a/7115547
// http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2019/p1406r0.html
template<typename... T>
struct std::hash<Tuple<T...>>
{
    template<typename E>
    std::size_t get_hash(const E& x) const
    {
        return std::hash<E>()(x);
    }

    template<std::size_t I>
    void combine_hash(std::size_t& seed, const Tuple<T...>& x) const
    {
        seed ^= get_hash(std::get<I>(x)) + 0x9e3779b9 + (seed << 6) + (seed >> 2);
        if constexpr(I+1 < sizeof...(T)) {
            combine_hash<I+1>(seed, x);
        }
    }

    std::size_t operator () (const Tuple<T...>& x) const
    {
        std::size_t seed = 0;
        combine_hash<0>(seed, x);
        return seed;
    }
};

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

Rat floordiv(const Rat& a, const Rat& b)
{
    if (b.numerator.sign < 0) {
        return floordiv(-a, -b);
    }
    bigint c = a.numerator * b.denominator;
    bigint d = b.numerator * a.denominator;
    if (c.sign < 0) {
        c -= d - 1;
    }
    Rat r;
    r.numerator = c / d;
    return r;
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

Rat mod(const Rat& a, const Rat& b)
{
    if (b.numerator.sign < 0) {
        return -mod(-a, -b);
    }
    Rat r = a % b;
    if (r.numerator.sign < 0) {
        r += b;
    }
    return r;
}

Int pow(Int b, Int e)
{
    if (e < 0) {
        return b == -1 && e % 2 == -1 ? -1 : b == 1 || b == -1 ? 1 : 0;
    }
    Int r = 1;
    while (e > 0) {
        if (e & 1) {
            r *= b;
        }
        b *= b;
        e >>= 1;
    }
    return r;
}

Rat pow(Rat b, Int e)
{
    if (e < 0) {
       std::swap(b.numerator, b.denominator);
       e = -e;
    }
    Rat r = 1;
    while (e > 0) {
        if (e & 1) {
            r *= b;
        }
        b *= b;
        e >>= 1;
    }
    return r;
}

/* Container operators */

String concat(const String& a, const String& b)
{
    return make_string(*a + *b);
}

template <typename T>
Array<T> concat(const Array<T>& a, const Array<T>& b)
{
    auto r = make_array<T>(*a);
    r->insert(r->end(), b->begin(), b->end());
    return r;
}

template <typename T>
Set<T> concat(const Set<T>& a, const Set<T>& b)
{
    auto r = make_set<T>(*a);
    r->insert(b->begin(), b->end());
    return r;
}

template <typename K, typename V>
Dict<K, V> concat(const Dict<K, V>& a, const Dict<K, V>& b)
{
    auto r = make_dict<K, V>(*a);
    for (auto&& e: *b) {
        r->insert_or_assign(e.first, e.second);
    }
    return r;
}

template <typename T>
Set<T> difference(const Set<T>& a, const Set<T>& b)
{
    auto r = make_set<T>();
    // https://stackoverflow.com/a/22711060
    std::copy_if(a->begin(), a->end(), std::inserter(*r, r->begin()),
                 [&b](const T& e) { return b->find(e) == b->end(); });
    return r;
}

template <typename T>
Set<T> intersection(const Set<T>& a, const Set<T>& b)
{
    auto r = make_set<T>();
    std::copy_if(a->begin(), a->end(), std::inserter(*r, r->begin()),
                 [&b](const T& e) { return b->find(e) != b->end(); });
    return r;
}

template <typename T>
Set<T> symmetric_difference(const Set<T>& a, const Set<T>& b)
{
    auto r = make_set<T>();
    std::copy_if(a->begin(), a->end(), std::inserter(*r, r->begin()),
                 [&b](const T& e) { return b->find(e) == b->end(); });
    std::copy_if(b->begin(), b->end(), std::inserter(*r, r->begin()),
                 [&a](const T& e) { return a->find(e) == a->end(); });
    return r;
}

template <typename T>
T multiply(const T& v, Int m)
{
    m = std::max(m, 0LL);
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


/* Container methods */

template <typename T, std::enable_if_t<std::is_same<typename T::value_type, Char>::value, int> = 0>
String join(const custom_ptr<T>& x, const String& sep)
{
    auto r = make_string();
    for (auto it = x->begin(); it != x->end(); ++it) {
        if (it != x->begin()) {
            r->append(*sep);
        }
        r->push_back(*it);
    }
    return r;
}

template <typename T, std::enable_if_t<std::is_same<typename T::value_type, String>::value, int> = 0>
String join(const custom_ptr<T>& x, const String& sep)
{
    auto r = make_string();
    for (auto it = x->begin(); it != x->end(); ++it) {
        if (it != x->begin()) {
            r->append(*sep);
        }
        r->append(**it);
    }
    return r;
}

template <typename T>
String asString(const custom_ptr<T>& x)
{
    return make_string(x->begin(), x->end());
}

/* String methods */

Array<String> split(const String& x, const String& y)
{
    auto r = make_array<String>();
    std::size_t start = 0;
    while (true) {
        auto end = x->find(*y, start);
        if (y->empty()) {
            end += 1;
        } else if (end == std::string::npos) {
            end = x->size();
        }
        r->push_back(make_string(x->substr(start, end-start)));
        if (end == x->size()) {
            return r;
        }
        start = end + y->size();
    }
}

Nullable<Int> find(const String& x, const String& y, Int i)
{
    if (i < 0) {
        i += x->size();
    }
    auto p = x->find(*y, i);
    if (p != std::string::npos) {
        return Nullable<Int>(p);
    } else {
        return Nullable<Int>();
    }
}

Int count(const String& x, Char e)
{
    return std::count(x->begin(), x->end(), e);
}

Bool startswith(const String& x, const String& y)
{
    return x->rfind(*y, 0) == 0;
}

Bool endswith(const String& x, const String& y)
{
    return x->find(*y, x->size() - y->size()) != std::string::npos;
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
Nullable<T> get(const Array<T>& x, Int i)
{
    if (i < 0) {
        i += x->size();
    }
    if (0 <= i && i < x->size()) {
        return Nullable<T>((*x)[i]);
    } else {
        return Nullable<T>();
    }
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

template <typename T, typename K>
Void sort(const Array<T>& v, Bool reverse, std::function<K(T)> key)
{
    if (reverse) {
        std::stable_sort(v->begin(), v->end(), [&](const T& x, const T& y) { return key(x) > key(y); });
    } else {
        std::stable_sort(v->begin(), v->end(), [&](const T& x, const T& y) { return key(x) < key(y); });
    }
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

/* Set methods */

template <typename T>
Void add(const Set<T>& x, const T& e)
{
    x->insert(e);
}

template <typename T>
Void union_(const Set<T>& x, const Set<T>& y)
{
    x->insert(y->begin(), y->end());
}

template <typename T>
Void subtract(const Set<T>& x, const Set<T>& y)
{
    for (auto&& e: *y) {
        x->erase(e);
    }
}

template <typename T>
Void intersect(const Set<T>& x, const Set<T>& y)
{
    subtract(x, difference(x, y));
}

template <typename T>
T pop(const Set<T>& x)
{
    auto r = *x->begin();
    x->erase(r);
    return r;
}

template <typename T>
Void remove(const Set<T>& x, const T& e)
{
    x->erase(e);
}

template <typename T>
Void clear(const Set<T>& x)
{
    x->clear();
}

template <typename T>
Set<T> copy(const Set<T>& x)
{
    return make_set<T>(*x);
}

template <typename T>
bool contains(const Set<T>& x, const T& e)
{
    return x->find(e) != x->end();
}

/* Dict methods */

template <typename K, typename V>
Void update(const Dict<K, V>& x, const Dict<K, V>& y)
{
    for (auto&& e: *y) {
        x->insert_or_assign(e.first, e.second);
    }
}

template <typename K, typename V>
Nullable<V> get(const Dict<K, V>& x, const K& e)
{
    auto it = x->find(e);
    if (it != x->end()) {
        return Nullable<V>(it->second);
    } else {
        return Nullable<V>();
    }
}

template <typename K, typename V>
Nullable<V> pop(const Dict<K, V>& x, const K& e)
{
    Nullable<V> r;
    auto it = x->find(e);
    if (it != x->end()) {
        r = Nullable<V>(it->second);
        x->erase(it);
    }
    return r;
}

template <typename K, typename V>
Void clear(const Dict<K, V>& x)
{
    x->clear();
}

template <typename K, typename V>
Dict<K, V> copy(const Dict<K, V>& x)
{
    return make_dict<K, V>(*x);
}


/* Conversion to String */

template <typename T> String toString(const Array<T>& x);
template <typename T> String toString(const Set<T>& x);
template <typename K, typename V> String toString(const Dict<K, V>& x);
template <typename T> String toString(const Nullable<T>& x);
template <std::size_t I = 0, typename... T> String toString(const Tuple<T...>& x);
template <typename T> String toString(const Object<T>& x);

String toString(Int x)
{
    return make_string(std::to_string(x));
}

String toString(const Rat& x)
{
    auto r = make_string(x.numerator.to_string());
    if (x.denominator > 1) {
        r->append("/");
        r->append(x.denominator.to_string());
    }
    return r;
}

String toString(Float x)
{
    static char buffer[25];
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

template <typename K, typename V>
String toString(const Dict<K, V>& x)
{
    if (x->empty()) {
        return make_string("{:}");
    }
    auto r = make_string();
    r->append("{");
    for (auto it = x->begin(); it != x->end(); ++it) {
        if (it != x->begin()) {
            r->append(", ");
        }
        r->append(*toString(it->first));
        r->append(": ");
        r->append(*toString(it->second));
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

template <std::size_t I /* = 0 is already in the declaration */, typename... T>
String toString(const Tuple<T...>& x)
{
    // https://stackoverflow.com/a/54225452
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

Int toInt(const Rat& x)
{
    return x.numerator.longValue() / x.denominator.longValue();
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
    return std::stoll(*x);
}

Int toInt(Char x)
{
    return toInt(toString(x));
}

/* Conversion to Rat */

Rat toRat(Int x)
{
    return Rat(x);
}

Rat toRat(const Rat& x)
{
    return x;
}

Rat toRat(Bool x)
{
    return x ? 1 : 0;
}

Rat toRat(const String& x)
{
    return Rat(*x);
}

Rat toRat(Char x)
{
    return toRat(toString(x));
}

/* Conversion to Float */

Float toFloat(Int x)
{
    return static_cast<Float>(x);
}

Float toFloat(const Rat& x)
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
    return std::stod(*x);
}

Float toFloat(Char x)
{
    return toFloat(toString(x));
}


/* Standard output */

template <typename T>
void write(const T& x)
{
    std::cout << *toString(x);
}

/* Standard input */

String read()
{
    auto r = make_string();
    std::cin >> *r;
    return r;
}

String readLine()
{
    auto r = make_string();
    std::getline(std::cin, *r);
    return r;
}

Int readInt()
{
    Int r;
    std::cin >> r;
    return r;
}

Rat readRat()
{
    return Rat(*read());
}

Float readFloat()
{
    Float r;
    std::cin >> r;
    return r;
}

Char readChar()
{
    Char r;
    std::cin >> r;
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
