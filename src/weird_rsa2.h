#ifndef WEIRD_RSA_CRT_H
#define WEIRD_RSA_CRT_H

#include <gmpxx.h>
#include <string>

// Perform RSA decryption using dp, dq, p, q, and ciphertext
mpz_class decrypt_with_dp_dq(const mpz_class& c, const mpz_class& p, const mpz_class& q,
                             const mpz_class& dp, const mpz_class& dq);

// Optional: converts hex string to ASCII
std::string hex_to_ascii_crt(const std::string& hex);

#endif // WEIRD_RSA_CRT_H
