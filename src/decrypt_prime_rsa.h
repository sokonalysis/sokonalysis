#ifndef DECRYPT_PRIME_RSA_H
#define DECRYPT_PRIME_RSA_H

#include <string>
#include <gmpxx.h>

class RSADecryptor {
public:
    RSADecryptor(const std::string& n_str, const std::string& c_str, unsigned long e_val);
    std::string decrypt();

private:
    mpz_class n, c;
    unsigned long e;
};

#endif // DECRYPT_PRIME_RSA_H
