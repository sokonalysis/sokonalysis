// PolyCipher.h
#ifndef POLYCIPHER_H
#define POLYCIPHER_H

#include <vector>
#include <string>

class PolyCipher {
public:
    PolyCipher(const std::vector<int>& shifts, const std::vector<int>& sequence);

    std::string encrypt(const std::string& plaintext);
    std::string decrypt(const std::string& ciphertext);

private:
    std::vector<int> shiftValues;
    std::vector<int> keySequence;

    char shiftChar(char c, int shift);
};

#endif
