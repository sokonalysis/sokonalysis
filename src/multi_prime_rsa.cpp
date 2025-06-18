#include "multi_prime_rsa.h"

RSACubeRootDecryptor::RSACubeRootDecryptor(const mpz_class& e_, const mpz_class& n_, const mpz_class& c_)
    : e(e_), n(n_), c(c_) {}

mpz_class RSACubeRootDecryptor::nthRoot(const mpz_class& value, unsigned long n) {
    mpz_class low = 0, high = value, mid, pow;
    while (low < high) {
        mid = (low + high) / 2;
        mpz_pow_ui(pow.get_mpz_t(), mid.get_mpz_t(), n);

        if (pow == value) return mid;
        if (pow < value) low = mid + 1;
        else high = mid;
    }
    return low - 1;
}

mpz_class RSACubeRootDecryptor::decrypt() {
    m = nthRoot(c, e.get_ui());  // Only safe if message^e < n
    return m;
}

std::string RSACubeRootDecryptor::decryptToAscii() {
    if (m == 0) decrypt();
    std::string ascii;
    mpz_class temp = m;
    while (temp > 0) {
        char ch = static_cast<char>(mpz_class(temp % 256).get_ui());
        ascii = ch + ascii;
        temp /= 256;
    }
    return ascii;
}
