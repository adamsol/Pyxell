
#include <cstdio>
#include <string>
#include <tuple>

using namespace std::string_literals;


void write(long long x)
{
    printf("%lld", x);
}

void write(double x)
{
    printf("%.15g", x);
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
