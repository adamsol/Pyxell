#include <complex>
#include <vector>

// Fast Fourier transform
// https://cp-algorithms.com/algebra/fft.html
// https://drive.google.com/file/d/1B9BIfATnI_qL6rYiE5hY9bh20SMVmHZ7/view

using cpx = std::complex<double>;
const double PI = acos(-1);
std::vector<cpx> roots = {{0, 0},
                     {1, 0}};

void ensure_capacity(int min_capacity) {
    for (int len = roots.size(); len < min_capacity; len *= 2) {
        for (int i = len >> 1; i < len; i++) {
            roots.emplace_back(roots[i]);
            double angle = 2 * PI * (2 * i + 1 - len) / (len * 2);
            roots.emplace_back(cos(angle), sin(angle));
        }
    }
}

void fft(std::vector<cpx> &z, bool inverse) {
    int n = z.size();
    // assert((n & (n - 1)) == 0);
    ensure_capacity(n);
    for (unsigned i = 1, j = 0; i < n; i++) {
        int bit = n >> 1;
        for (; j >= bit; bit >>= 1)
            j -= bit;
        j += bit;
        if (i < j)
            swap(z[i], z[j]);
    }
    for (int len = 1; len < n; len <<= 1) {
        for (int i = 0; i < n; i += len * 2) {
            for (int j = 0; j < len; j++) {
                cpx root = inverse ? conj(roots[j + len]) : roots[j + len];
                cpx u = z[i + j];
                cpx v = z[i + j + len] * root;
                z[i + j] = u + v;
                z[i + j + len] = u - v;
            }
        }
    }
    if (inverse)
        for (int i = 0; i < n; i++)
            z[i] /= n;
}

std::vector<int> multiply_bigint(const std::vector<int> &a, const std::vector<int> &b, int base) {
    int need = a.size() + b.size();
    int n = 1;
    while (n < need) n <<= 1;
    std::vector<cpx> p(n);
    for (size_t i = 0; i < n; i++) {
        p[i] = cpx(i < a.size() ? a[i] : 0, i < b.size() ? b[i] : 0);
    }
    fft(p, false);
    // a[w[k]] = (p[w[k]] + conj(p[w[n-k]])) / 2
    // b[w[k]] = (p[w[k]] - conj(p[w[n-k]])) / (2*i)
    std::vector<cpx> ab(n);
    cpx r(0, -0.25);
    for (int i = 0; i < n; i++) {
        int j = (n - i) & (n - 1);
        ab[i] = (p[i] * p[i] - conj(p[j] * p[j])) * r;
    }
    fft(ab, true);
    std::vector<int> result(need);
    long long carry = 0;
    for (int i = 0; i < need; i++) {
        long long d = (long long) (ab[i].real() + 0.5) + carry;
        carry = d / base;
        result[i] = d % base;
    }
    return result;
}
