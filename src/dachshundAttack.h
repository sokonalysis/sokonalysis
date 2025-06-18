#ifndef WIENER_H
#define WIENER_H

#include <gmpxx.h>

mpz_class wienerAttack(const mpz_class& e, const mpz_class& n);
std::string decryptRSA(const mpz_class& c, const mpz_class& d, const mpz_class& n);

#endif
