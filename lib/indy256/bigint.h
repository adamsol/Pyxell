
#include <algorithm>
#include <string>
#include <vector>

#include "fft.h"

constexpr int digits(int base) noexcept {
    return base <= 1 ? 0 : 1 + digits(base / 10);
}

constexpr int base = 1000'000'000;
constexpr int base_digits = digits(base);

constexpr int fft_base = 10'000;  // fft_base^2 * n / fft_base_digits <= 10^15 for double
constexpr int fft_base_digits = digits(fft_base);

struct bigint {
    // value == 0 is represented by empty z
    std::vector<int> z;  // digits

    // sign == 1 <==> value >= 0
    // sign == -1 <==> value < 0
    int sign;

    bigint(long long v = 0) { *this = v; }

    bigint &operator=(long long v) {
        sign = v < 0 ? -1 : 1;
        v *= sign;
        z.clear();
        for (; v > 0; v = v / base)
            z.push_back((int)(v % base));
        return *this;
    }

    bigint(const std::string &s) { read(s); }

    bigint &operator+=(const bigint &other) {
        if (sign == other.sign) {
            for (int i = 0, carry = 0; i < other.z.size() || carry; ++i) {
                if (i == z.size())
                    z.push_back(0);
                z[i] += carry + (i < other.z.size() ? other.z[i] : 0);
                carry = z[i] >= base;
                if (carry)
                    z[i] -= base;
            }
        } else if (other != 0 /* prevent infinite loop */) {
            *this -= -other;
        }
        return *this;
    }

    friend bigint operator+(bigint a, const bigint &b) {
        a += b;
        return a;
    }

    bigint &operator-=(const bigint &other) {
        if (sign == other.sign) {
            if ((sign == 1 && *this >= other) || (sign == -1 && *this <= other)) {
                for (int i = 0, carry = 0; i < other.z.size() || carry; ++i) {
                    z[i] -= carry + (i < other.z.size() ? other.z[i] : 0);
                    carry = z[i] < 0;
                    if (carry)
                        z[i] += base;
                }
                trim();
            } else {
                *this = other - *this;
                this->sign = -this->sign;
            }
        } else {
            *this += -other;
        }
        return *this;
    }

    friend bigint operator-(bigint a, const bigint &b) {
        a -= b;
        return a;
    }

    bigint &operator*=(int v) {
        if (v < 0)
            sign = -sign, v = -v;
        for (int i = 0, carry = 0; i < z.size() || carry; ++i) {
            if (i == z.size())
                z.push_back(0);
            long long cur = (long long)z[i] * v + carry;
            carry = (int)(cur / base);
            z[i] = (int)(cur % base);
        }
        trim();
        return *this;
    }

    bigint operator*(int v) const { return bigint(*this) *= v; }

    friend std::pair<bigint, bigint> divmod(const bigint &a1, const bigint &b1) {
        int norm = base / (b1.z.back() + 1);
        bigint a = a1.abs() * norm;
        bigint b = b1.abs() * norm;
        bigint q, r;
        q.z.resize(a.z.size());

        for (int i = (int)a.z.size() - 1; i >= 0; i--) {
            r *= base;
            r += a.z[i];
            int s1 = b.z.size() < r.z.size() ? r.z[b.z.size()] : 0;
            int s2 = b.z.size() - 1 < r.z.size() ? r.z[b.z.size() - 1] : 0;
            int d = (int)(((long long)s1 * base + s2) / b.z.back());
            r -= b * d;
            while (r < 0)
                r += b, --d;
            q.z[i] = d;
        }

        q.sign = a1.sign * b1.sign;
        r.sign = a1.sign;
        q.trim();
        r.trim();
        return {q, r / norm};
    }

    bigint operator/(const bigint &v) const { return divmod(*this, v).first; }

    bigint operator%(const bigint &v) const { return divmod(*this, v).second; }

    bigint &operator/=(int v) {
        if (v < 0)
            sign = -sign, v = -v;
        for (int i = (int)z.size() - 1, rem = 0; i >= 0; --i) {
            long long cur = z[i] + rem * (long long)base;
            z[i] = (int)(cur / v);
            rem = (int)(cur % v);
        }
        trim();
        return *this;
    }

    bigint operator/(int v) const { return bigint(*this) /= v; }

    int operator%(int v) const {
        if (v < 0)
            v = -v;
        int m = 0;
        for (int i = (int)z.size() - 1; i >= 0; --i)
            m = (int)((z[i] + m * (long long)base) % v);
        return m * sign;
    }

    bigint &operator*=(const bigint &v) {
        *this = *this * v;
        return *this;
    }

    bigint &operator/=(const bigint &v) {
        *this = *this / v;
        return *this;
    }

    bigint &operator%=(const bigint &v) {
        *this = *this % v;
        return *this;
    }

    bool operator<(const bigint &v) const {
        if (sign != v.sign)
            return sign < v.sign;
        if (z.size() != v.z.size())
            return z.size() * sign < v.z.size() * v.sign;
        for (int i = (int)z.size() - 1; i >= 0; i--)
            if (z[i] != v.z[i])
                return z[i] * sign < v.z[i] * sign;
        return false;
    }

    bool operator>(const bigint &v) const { return v < *this; }

    bool operator<=(const bigint &v) const { return !(v < *this); }

    bool operator>=(const bigint &v) const { return !(*this < v); }

    bool operator==(const bigint &v) const { return sign == v.sign && z == v.z; }

    bool operator!=(const bigint &v) const { return !(*this == v); }

    void trim() {
        while (!z.empty() && z.back() == 0)
            z.pop_back();
        if (z.empty())
            sign = 1;
    }

    bool isZero() const { return z.empty(); }

    friend bigint operator-(bigint v) {
        if (!v.z.empty())
            v.sign = -v.sign;
        return v;
    }

    bigint abs() const { return sign == 1 ? *this : -*this; }

    long long longValue() const {
        long long res = 0;
        for (int i = (int)z.size() - 1; i >= 0; i--)
            res = res * base + z[i];
        return res * sign;
    }

    double doubleValue() const {
        double res = 0.0;
        for (int i = (int)z.size() - 1; i >= 0; i--)
            res = res * base + z[i];
        return res * sign;
    }

    friend bigint gcd(const bigint &a, const bigint &b) { return b.isZero() ? a : gcd(b, a % b); }

    friend bigint lcm(const bigint &a, const bigint &b) { return a / gcd(a, b) * b; }

    void read(const std::string &s) {
        sign = 1;
        z.clear();
        int pos = 0;
        while (pos < s.size() && (s[pos] == '-' || s[pos] == '+')) {
            if (s[pos] == '-')
                sign = -sign;
            ++pos;
        }
        for (int i = (int)s.size() - 1; i >= pos; i -= base_digits) {
            int x = 0;
            for (int j = std::max(pos, i - base_digits + 1); j <= i; j++)
                x = x * 10 + s[j] - '0';
            z.push_back(x);
        }
        trim();
    }

    std::string to_string() const {
        if (z.empty()) {
            return "0";
        } else {
            std::string s;
            for (int digit : z) {
                for (int i = 0; i < base_digits; ++i) {
                    s.push_back('0' + digit % 10);
                    digit /= 10;
                }
            }
            while (s.back() == '0') {
                s.pop_back();
            }
            if (sign < 0) {
                s.push_back('-');
            }
            std::reverse(s.begin(), s.end());
            return s;
        }
    }

    static std::vector<int> convert_base(const std::vector<int> &a, int old_digits, int new_digits) {
        std::vector<long long> p(std::max(old_digits, new_digits) + 1);
        p[0] = 1;
        for (int i = 1; i < p.size(); i++)
            p[i] = p[i - 1] * 10;
        std::vector<int> res;
        long long cur = 0;
        int cur_digits = 0;
        for (int v : a) {
            cur += v * p[cur_digits];
            cur_digits += old_digits;
            while (cur_digits >= new_digits) {
                res.push_back(int(cur % p[new_digits]));
                cur /= p[new_digits];
                cur_digits -= new_digits;
            }
        }
        res.push_back((int)cur);
        while (!res.empty() && res.back() == 0)
            res.pop_back();
        return res;
    }

    bigint operator*(const bigint &v) const {
        if (std::min(z.size(), v.z.size()) < 150)
            return mul_simple(v);
        bigint res;
        res.sign = sign * v.sign;
        res.z = multiply_bigint(convert_base(z, base_digits, fft_base_digits),
                                convert_base(v.z, base_digits, fft_base_digits), fft_base);
        res.z = convert_base(res.z, fft_base_digits, base_digits);
        res.trim();
        return res;
    }

    bigint mul_simple(const bigint &v) const {
        bigint res;
        res.sign = sign * v.sign;
        res.z.resize(z.size() + v.z.size());
        for (int i = 0; i < z.size(); ++i)
            if (z[i])
                for (int j = 0, carry = 0; j < v.z.size() || carry; ++j) {
                    long long cur = res.z[i + j] + (long long)z[i] * (j < v.z.size() ? v.z[j] : 0) + carry;
                    carry = (int)(cur / base);
                    res.z[i + j] = (int)(cur % base);
                }
        res.trim();
        return res;
    }
};
