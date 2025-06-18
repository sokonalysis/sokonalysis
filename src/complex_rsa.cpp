#include "complex_rsa.h"
#include <iostream>
#include <vector>

// Continued fraction and convergents
static std::vector<std::pair<mpz_class, mpz_class>> compute_convergents(const mpz_class& e, const mpz_class& n) {
    std::vector<mpz_class> a;
    mpz_class q, r, t1 = e, t2 = n;

    while (t2 != 0) {
        q = t1 / t2;
        r = t1 % t2;
        a.push_back(q);
        t1 = t2;
        t2 = r;
    }

    std::vector<std::pair<mpz_class, mpz_class>> convs;
    mpz_class h1 = 1, h0 = 0, k1 = 0, k0 = 1;

    for (auto ai : a) {
        mpz_class h = ai * h1 + h0;
        mpz_class k = ai * k1 + k0;
        convs.emplace_back(h, k);
        h0 = h1; h1 = h;
        k0 = k1; k1 = k;
    }

    return convs;
}

// Decryption function using Wiener’s attack
std::string wiener_attack_decrypt(const mpz_class& n, const mpz_class& e1, const mpz_class& e2, const mpz_class& c) {
    mpz_class e = e1 * e2;
    auto convergents = compute_convergents(e, n);

    for (const auto& [k, d] : convergents) {
        if (k == 0) continue;

        mpz_class ed_minus_1 = e * d - 1;
        if (ed_minus_1 % k != 0) continue;

        mpz_class phi = ed_minus_1 / k;
        mpz_class s = n - phi + 1;
        mpz_class discr = s * s - 4 * n;
        if (discr < 0) continue;

        if (!mpz_perfect_square_p(discr.get_mpz_t())) continue;

        mpz_class sqrt_discr;
        mpz_sqrt(sqrt_discr.get_mpz_t(), discr.get_mpz_t());

        mpz_class p = (s + sqrt_discr) / 2;
        mpz_class q = (s - sqrt_discr) / 2;

        if (p * q != n) continue;

        // Decrypt using d
        mpz_class m;
        mpz_powm(m.get_mpz_t(), c.get_mpz_t(), d.get_mpz_t(), n.get_mpz_t());

        std::string hex_str = m.get_str(16);
        if (hex_str.size() % 2 != 0)
            hex_str = "0" + hex_str;

        std::string result;
        try {
            for (size_t i = 0; i < hex_str.size(); i += 2) {
                std::string byte_str = hex_str.substr(i, 2);
                char byte = static_cast<char>(std::stoul(byte_str, nullptr, 16));
                result.push_back(byte);
            }
        } catch (...) {
            continue; // silently skip bad conversions
        }

        if (result.find("CTF") != std::string::npos || result.find("flag") != std::string::npos) {
            std::cout << "[+] Decryption successful!\n";
            return result;
        }
    }

    std::cout << "[-] Failed to decrypt using Wiener’s attack.\n";
    return "";
}
