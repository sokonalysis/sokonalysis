#include "transposition.h"

// Function to encrypt using Transposition cipher
std::string transposition_encrypt(const std::string& message, int key) {
    int rows = (message.length() + key - 1) / key;
    std::string encrypted(message.length(), ' ');
    int index = 0;
    for (int col = 0; col < key; col++) {
        for (int row = 0; row < rows; row++) {
            int pos = row * key + col;
            if (pos < message.length()) {
                encrypted[index++] = message[pos];
            }
        }
    }
    return encrypted;
}

// Function to decrypt using Transposition cipher
std::string transposition_decrypt(const std::string& message, int key) {
    int rows = (message.length() + key - 1) / key;
    std::string decrypted(message.length(), ' ');
    int index = 0;
    for (int col = 0; col < key; col++) {
        for (int row = 0; row < rows; row++) {
            int pos = row * key + col;
            if (pos < message.length()) {
                decrypted[pos] = message[index++];
            }
        }
    }
    return decrypted;
}
