#ifndef RSA_CUBEROOT_H
#define RSA_CUBEROOT_H

#include <gmpxx.h>
#include <string>

class RSACubeRootDecryptor {
private:
    mpz_class e, n, c, m;

public:
    RSACubeRootDecryptor(const mpz_class& e_, const mpz_class& n_, const mpz_class& c_);
    mpz_class nthRoot(const mpz_class& value, unsigned long n);
    mpz_class decrypt();             // Returns integer m
    std::string decryptToAscii();    // Converts m to ASCII
};

#endif
