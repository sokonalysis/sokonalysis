#include "decrypt_prime_rsa.h"
#include <gmp.h>
#include <sstream>

RSADecryptor::RSADecryptor(const std::string& n_str, const std::string& c_str, unsigned long e_val)
    : n(n_str), c(c_str), e(e_val) { }

std::string RSADecryptor::decrypt() {
    mpz_class phi = n - 1;
    mpz_class d;

    // Compute modular inverse: d = e^-1 mod phi
    if (mpz_invert(d.get_mpz_t(), mpz_class(e).get_mpz_t(), phi.get_mpz_t()) == 0) {
        return "Modular inverse not found.";
    }

    // m = c^d mod n
    mpz_class m;
    mpz_powm(m.get_mpz_t(), c.get_mpz_t(), d.get_mpz_t(), n.get_mpz_t());

    // Convert m to string (plaintext)
    std::string hexStr = m.get_str(16); // hex
    if (hexStr.size() % 2) hexStr = "0" + hexStr; // pad for even length

    std::string plaintext;
    for (size_t i = 0; i < hexStr.length(); i += 2) {
        std::string byteStr = hexStr.substr(i, 2);
        char byte = static_cast<char>(strtol(byteStr.c_str(), nullptr, 16));
        plaintext += byte;
    }

    return plaintext;
}
