#include "decrypt_square_rsa.h"
#include <gmpxx.h>
#include <cstdlib>  // for free()

// Convert big integer to string using GMP mpz_export
static std::string bigintToString(const mpz_class& bigint) {
    size_t count = 0;
    void* data = mpz_export(nullptr, &count, 1, 1, 1, 0, bigint.get_mpz_t());

    std::string result((char*)data, count);
    free(data);
    return result;
}

std::string decryptRSASquareN(const std::string& c, const std::string& e, const std::string& p) {
    mpz_class c_num(c);
    mpz_class e_num(e);
    mpz_class p_num(p);

    // Compute n = p^2
    mpz_class n = p_num * p_num;

    // Compute phi(n) = p * (p - 1)
    mpz_class phi = p_num * (p_num - 1);

    // Compute d = e^(-1) mod phi(n)
    mpz_class d;
    if (mpz_invert(d.get_mpz_t(), e_num.get_mpz_t(), phi.get_mpz_t()) == 0) {
        // No inverse exists, return error message
        return "[Error] Modular inverse does not exist.";
    }

    // Decrypt plaintext: m = c^d mod n
    mpz_class m;
    mpz_powm(m.get_mpz_t(), c_num.get_mpz_t(), d.get_mpz_t(), n.get_mpz_t());

    // Convert bigint plaintext to string
    return bigintToString(m);
}
