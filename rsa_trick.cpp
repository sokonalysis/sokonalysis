#include "rsa_trick.h"
#include <cryptopp/nbtheory.h> // for a_exp_b_mod_c

using namespace CryptoPP;

RSAOracle::RSAOracle(const Integer& n, const Integer& e) : n_(n), e_(e) {
    Integer two(2);
    two_enc_ = a_exp_b_mod_c(two, e_, n_);
}

Integer RSAOracle::getModifiedCiphertext(const Integer& c) const {
    return (c * two_enc_) % n_;
}

Integer RSAOracle::recoverMessage(const Integer& m_prime) const {
    Integer two(2);
    return m_prime / two;
}

std::string RSAOracle::integerToString(const Integer& x) {
    size_t byteCount = x.MinEncodedSize(Integer::UNSIGNED);
    std::string bytes(byteCount, '\0');
    x.Encode((byte*)&bytes[0], byteCount, Integer::UNSIGNED);
    return bytes;
}
