#include "weird_rsa2.h"
#include <iostream>
#include <sstream>
#include <cstdlib>

mpz_class decrypt_with_dp_dq(const mpz_class& c, const mpz_class& p, const mpz_class& q,
                             const mpz_class& dp, const mpz_class& dq) {
    mpz_class m1, m2, qinv, h, m;

    // m1 = c^dp mod p
    mpz_powm(m1.get_mpz_t(), c.get_mpz_t(), dp.get_mpz_t(), p.get_mpz_t());

    // m2 = c^dq mod q
    mpz_powm(m2.get_mpz_t(), c.get_mpz_t(), dq.get_mpz_t(), q.get_mpz_t());

    // qinv = q^(-1) mod p
    mpz_invert(qinv.get_mpz_t(), q.get_mpz_t(), p.get_mpz_t());

    // h = (qinv * (m1 - m2)) % p
    h = (qinv * (m1 - m2)) % p;
    if (h < 0) h += p;

    // m = m2 + h * q
    m = m2 + h * q;

    return m;
}

std::string hex_to_ascii_crt(const std::string& hex) {
    std::string ascii;
    for (size_t i = 0; i < hex.length(); i += 2) {
        std::string byteStr = hex.substr(i, 2);
        char byte = static_cast<char>(strtol(byteStr.c_str(), nullptr, 16));
        ascii += byte;
    }
    return ascii;
}
