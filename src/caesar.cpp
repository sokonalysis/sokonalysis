#include "caesar.h"

// Function to encrypt using Caesar cipher
std::string caesar_encrypt(const std::string& message, int shift, int mapping) {
    std::string encrypted = "";
    for (char c : message) {
        if (isalpha(c)) {
            char base = isupper(c) ? 'A' : 'a';
            encrypted += char((c - base + shift) % 26 + base);
        } else {
            encrypted += c;
        }
    }
    return encrypted;
}

// Function to decrypt using Caesar cipher
std::string caesar_decrypt(const std::string& message, int shift, int mapping) {
    std::string decrypted = "";
    for (char c : message) {
        if (isalpha(c)) {
            char base = isupper(c) ? 'A' : 'a';  // Base for upper or lower case letters
            decrypted += char((c - base - shift + 26) % 26 + base);  // Reverse the shift for decryption
        } else {
            decrypted += c;  // Non-alphabet characters remain unchanged
        }
    }
    return decrypted;
}
