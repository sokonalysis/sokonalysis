#ifndef WEIRDER_RSA_H
#define WEIRDER_RSA_H

#include <gmpxx.h>

mpz_class reconstruct_private_key_and_decrypt(const mpz_class& e, const mpz_class& n, const mpz_class& dp, const mpz_class& c);
std::string hex_to_ascii(const std::string& hex);

#endif
