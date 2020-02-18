
#define _CRT_SECURE_NO_WARNINGS

#include <cmath>
#include <cstdio>
#include <functional>
#include <string>
#include <tuple>
#include <vector>

using namespace std::string_literals;

// https://github.com/godotengine/godot/pull/33376
#if defined(__MINGW32__) || (defined(_MSC_VER) && _MSC_VER < 1900 && defined(_TWO_DIGIT_EXPONENT)) && !defined(_UCRT)
	unsigned int old_exponent_format = _set_output_format(_TWO_DIGIT_EXPONENT);
#endif


/* Arithmetic operators */

long long floordiv(long long a, long long b)
{
    if (b < 0) {
        return floordiv(-a, -b);
    }
    if (a < 0) {
        a -= b - 1;
    }
    return a / b;
}

long long mod(long long a, long long b)
{
    if (b < 0) {
        return -mod(-a, -b);
    }
    long long r = a % b;
    if (r < 0) {
        r += b;
    }
    return r;
}

long long pow(long long b, long long e)
{
    if (e < 0) {
        return 0;
    }
    long long r = 1;
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

std::string asString(const std::vector<char>& x)
{
    return std::string(x.begin(), x.end());
}

template <typename T>
T concat(T a, const T& b) {
    a.insert(a.end(), b.begin(), b.end());
    return a;
}

template <typename T>
T extend(const T& a, long long m) {
    T r;
    r.reserve(a.size() * m);
    while (m--) {
        r.insert(r.end(), a.begin(), a.end());
    }
    return r;
}


/* Conversion to String */

char buffer[25];

std::string toString(long long x) {
    sprintf(buffer, "%lld", x);
    return std::string(buffer);
}

std::string toString(double x) {
    if (fabs(x) < 1e15 && floor(x) == x) {
        sprintf(buffer, "%.0f.0", x);
    } else {
        sprintf(buffer, "%.15g", x);
    }
    return std::string(buffer);
}

std::string toString(bool x) {
    return x ? "true" : "false";
}

std::string toString(char x) {
    return std::string(1, x);
}

const std::string& toString(const std::string& x) {
    return x;
}

template <typename T>
std::string toString(const std::vector<T>& x)
{
    std::string r;
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
std::string toString(const std::tuple<T...>& x)
{
    // https://stackoverflow.com/a/54225452/12643160
    std::string r;
    r.append(toString(std::get<I>(x)));
    if constexpr(I+1 < sizeof...(T)) {
        r.append(" ");
        r.append(toString<I+1>(x));
    }
    return r;
}


/* Conversion to Int */

long long toInt(long long x) {
    return x;
}

long long toInt(double x) {
    return static_cast<long long>(x);
}

long long toInt(bool x) {
    return x ? 1 : 0;
}

long long toInt(const std::string& x) {
    long long r;
    sscanf(x.c_str(), "%lld", &r);
    return r;
}

long long toInt(char x) {
    return toInt(toString(x));
}


/* Conversion to Float */

double toFloat(long long x) {
    return static_cast<double>(x);
}

double toFloat(double x) {
    return x;
}

double toFloat(bool x) {
    return x ? 1.0 : 0.0;
}

double toFloat(const std::string& x) {
    double r;
    sscanf(x.c_str(), "%lg", &r);
    return r;
}

double toFloat(char x) {
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

std::string read()
{
    scanf("%1023s", input);
    return std::string(input);
}

std::string readLine()
{
    scanf("%1023[^\n]%*c", input);
    return std::string(input);
}

long long readInt()
{
    long long r;
    scanf("%lld", &r);
    return r;
}

double readFloat()
{
    double r;
    scanf("%lg", &r);
    return r;
}

char readChar()
{
    char r;
    scanf("%c", &r);
    return r;
}
