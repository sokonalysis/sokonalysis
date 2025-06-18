#ifndef RSA_LOW_EXP_H
#define RSA_LOW_EXP_H

#include <gmpxx.h>
#include <string>

class RSALowExpDecryptor {
public:
    RSALowExpDecryptor(const mpz_class& n, const mpz_class& e, const mpz_class& c);
    mpz_class decrypt();
    std::string decryptToAscii();

private:
    mpz_class nthRoot(const mpz_class& value, unsigned long n);

    mpz_class n;
    mpz_class e;
    mpz_class c;
    mpz_class m;
};

#endif // RSA_LOW_EXP_H
