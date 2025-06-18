#include "hastad.h"
#include <gmpxx.h>
#include <vector>
#include <string>

mpz_class chinese_remainder(const std::vector<mpz_class>& c, const std::vector<mpz_class>& n) {
    mpz_class N = 1;
    for (const auto& ni : n) N *= ni;

    mpz_class result = 0;
    for (size_t i = 0; i < c.size(); ++i) {
        mpz_class Ni = N / n[i];
        mpz_class ui;
        mpz_invert(ui.get_mpz_t(), Ni.get_mpz_t(), n[i].get_mpz_t());
        result += c[i] * Ni * ui;
    }

    return result % N;
}

mpz_class integer_nth_root(mpz_class x, unsigned int n) {
    mpz_class low = 0, high = x, mid, mid_pow;

    while (low < high) {
        mid = (low + high) / 2;
        mpz_pow_ui(mid_pow.get_mpz_t(), mid.get_mpz_t(), n);

        if (mid_pow < x)
            low = mid + 1;
        else
            high = mid;
    }

    mpz_pow_ui(mid_pow.get_mpz_t(), high.get_mpz_t(), n);
    if (mid_pow > x)
        return high - 1;
    else
        return high;
}

std::string decrypt_message(const std::vector<mpz_class>& c, const std::vector<mpz_class>& n, unsigned int e) {
    mpz_class M = chinese_remainder(c, n);
    mpz_class m = integer_nth_root(M, e);

    std::string hex = m.get_str(16);
    if (hex.size() % 2 != 0) hex = "0" + hex;  // pad if odd-length

    std::string result;
    for (size_t i = 0; i < hex.length(); i += 2) {
        std::string byte = hex.substr(i, 2);
        char ch = static_cast<char>(strtol(byte.c_str(), nullptr, 16));
        result.push_back(ch);
    }

    return result;
}
