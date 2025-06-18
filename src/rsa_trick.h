#ifndef RSA_ORACLE_H
#define RSA_ORACLE_H

#include <cryptopp/integer.h>
#include <string>

class RSAOracle {
public:
    RSAOracle(const CryptoPP::Integer& n, const CryptoPP::Integer& e);

    // Given ciphertext c, return modified ciphertext c' = c * (2^e) mod n
    CryptoPP::Integer getModifiedCiphertext(const CryptoPP::Integer& c) const;

    // Given oracle decrypted m_prime, compute original message m = m_prime / 2
    CryptoPP::Integer recoverMessage(const CryptoPP::Integer& m_prime) const;

    // Convert Integer to printable string
    static std::string integerToString(const CryptoPP::Integer& x);

private:
    CryptoPP::Integer n_;
    CryptoPP::Integer e_;
    CryptoPP::Integer two_enc_;  // 2^e mod n
};

#endif
