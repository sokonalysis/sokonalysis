#include "dachshundAttack.h"
#include <vector>
#include <string>
#include <iostream>

// Continued fraction expansion of e/n
std::vector<mpz_class> continuedFraction(const mpz_class& e, const mpz_class& n) {
    std::vector<mpz_class> cf;
    mpz_class a = e, b = n, q, r;
    while (b != 0) {
        q = a / b;
        r = a % b;
        cf.push_back(q);
        a = b;
        b = r;
    }
    return cf;
}

// Compute convergents from continued fraction
std::vector<std::pair<mpz_class, mpz_class>> convergents(const std::vector<mpz_class>& cf) {
    std::vector<std::pair<mpz_class, mpz_class>> conv;
    mpz_class num_prev = 0, num = 1;
    mpz_class den_prev = 1, den = 0;

    for (auto q : cf) {
        mpz_class num_next = q * num + num_prev;
        mpz_class den_next = q * den + den_prev;
        conv.push_back({num_next, den_next});
        num_prev = num;
        num = num_next;
        den_prev = den;
        den = den_next;
    }
    return conv;
}

mpz_class wienerAttack(const mpz_class& e, const mpz_class& n) {
    auto cf = continuedFraction(e, n);
    auto conv = convergents(cf);

    for (auto& frac : conv) {
        mpz_class k = frac.first;
        mpz_class d = frac.second;
        if (k == 0) continue;

        // Check if (e*d - 1) % k == 0 to find phi
        mpz_class phi_candidate;
        mpz_class ed_minus_1 = e * d - 1;
        if (ed_minus_1 % k != 0) continue;
        phi_candidate = ed_minus_1 / k;

        // Solve quadratic x^2 - (n - phi + 1)x + n = 0
        mpz_class a = 1;
        mpz_class b = -(n - phi_candidate + 1);
        mpz_class c = n;

        // discriminant = b^2 - 4ac
        mpz_class discr = b * b - 4 * a * c;
        if (discr < 0) continue;

        // sqrt of discriminant
        mpz_class sqrt_discr;
        if (!mpz_perfect_square_p(discr.get_mpz_t())) continue;
        mpz_sqrt(sqrt_discr.get_mpz_t(), discr.get_mpz_t());

        // roots = (b ± sqrt_discr) / 2a
        mpz_class root1 = (-b + sqrt_discr) / 2;
        mpz_class root2 = (-b - sqrt_discr) / 2;

        if (root1 * root2 == n) {
            // valid d found
            return d;
        }
    }
    return 0; // attack failed
}

std::string decryptRSA(const mpz_class& c, const mpz_class& d, const mpz_class& n) {
    mpz_class m;
    mpz_powm(m.get_mpz_t(), c.get_mpz_t(), d.get_mpz_t(), n.get_mpz_t());

    // Convert number m to bytes (big-endian)
    size_t count = (mpz_sizeinbase(m.get_mpz_t(), 2) + 7) / 8;
    std::string result(count, '\0');
    mpz_export(&result[0], nullptr, 1, 1, 1, 0, m.get_mpz_t());

    return result;
}
