// PolyCipher.cpp
#include "caesar_sequence.h"
#include <iostream>
#include <cctype>

PolyCipher::PolyCipher(const std::vector<int>& shifts, const std::vector<int>& sequence)
    : shiftValues(shifts), keySequence(sequence) {}

char PolyCipher::shiftChar(char c, int shift) {
    if (!std::isalpha(c)) return c;

    char base = std::isupper(c) ? 'A' : 'a';
    return static_cast<char>((c - base + shift + 26) % 26 + base);
}

std::string PolyCipher::encrypt(const std::string& plaintext) {
    std::string result;
    for (size_t i = 0; i < plaintext.size(); ++i) {
        int shift = shiftValues[keySequence[i % keySequence.size()]];
        result += shiftChar(plaintext[i], shift);
    }
    return result;
}

std::string PolyCipher::decrypt(const std::string& ciphertext) {
    std::string result;
    for (size_t i = 0; i < ciphertext.size(); ++i) {
        int shift = shiftValues[keySequence[i % keySequence.size()]];
        result += shiftChar(ciphertext[i], -shift);
    }
    return result;
}
