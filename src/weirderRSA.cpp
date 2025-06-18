#include "weirderRSA.h"
#include <iostream>
#include <sstream>
#include <gmpxx.h>

mpz_class reconstruct_private_key_and_decrypt(const mpz_class& e, const mpz_class& n, const mpz_class& dp, const mpz_class& c) {
    mpz_class p, q, d, phi;
    bool found = false;

    for (mpz_class kp = 1; kp < e; kp++) {
        mpz_class numerator = e * dp - 1;
        if (numerator % kp != 0) continue;

        mpz_class candidate_p = numerator / kp + 1;

        if (n % candidate_p == 0) {
            p = candidate_p;
            found = true;
            break;
        }
    }

    if (!found) {
        std::cerr << "Failed to reconstruct p.\n";
        return 0;
    }

    q = n / p;
    phi = (p - 1) * (q - 1);
    mpz_invert(d.get_mpz_t(), e.get_mpz_t(), phi.get_mpz_t());

    mpz_class m;
    mpz_powm(m.get_mpz_t(), c.get_mpz_t(), d.get_mpz_t(), n.get_mpz_t());

    return m;
}

std::string hex_to_ascii(const std::string& hex) {
    std::string ascii;
    for (size_t i = 0; i < hex.length(); i += 2) {
        std::string byteStr = hex.substr(i, 2);
        char byte = static_cast<char>(strtol(byteStr.c_str(), nullptr, 16));
        ascii += byte;
    }
    return ascii;
}
