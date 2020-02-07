
#include <cmath>
#include <cstdio>
#include <string>
#include <tuple>

using namespace std::string_literals;

// https://github.com/godotengine/godot/pull/33376
#if defined(__MINGW32__) || (defined(_MSC_VER) && _MSC_VER < 1900 && defined(_TWO_DIGIT_EXPONENT)) && !defined(_UCRT)
	unsigned int old_exponent_format = _set_output_format(_TWO_DIGIT_EXPONENT);
#endif


/* Mathematics */

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


/* Standard output */

void write(long long x)
{
    printf("%lld", x);
}

void write(double x)
{
    if (fabs(x) < 1e15 && floor(x) == x) {
        printf("%.0f.0", x);
    } else {
        printf("%.15g", x);
    }
}

void write(bool x)
{
    printf(x ? "true" : "false");
}

void write(char x)
{
    printf("%c", x);
}

void write(const std::string& x)
{
    printf("%s", x.c_str());
}

template <std::size_t I = 0, typename... T>
void write(const std::tuple<T...>& x)
{
    // https://stackoverflow.com/a/54225452/12643160
    write(std::get<I>(x));
    if constexpr(I+1 < sizeof...(T)) {
        printf(" ");
        write<I+1>(x);
    }
}
