#ifndef WIENER_ATTACK_H
#define WIENER_ATTACK_H

#include <string>
#include <gmpxx.h>

std::string wiener_attack_decrypt(const mpz_class& n, const mpz_class& e1, const mpz_class& e2, const mpz_class& c);

#endif // WIENER_ATTACK_H
