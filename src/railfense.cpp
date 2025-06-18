#include "railfence.h"
#include <vector>

// Rail Fence Cipher encryption
std::string rail_fence_encrypt(const std::string &message, int key) {
    if (key <= 1) return message;  // No encryption needed for 1 or less rails

    // Create a 2D array to store the rails
    std::vector<std::vector<char>> rail(key, std::vector<char>(message.length(), '\n'));
    int row = 0;
    bool down = false;  // Direction flag

    // Fill the rail array following the zigzag pattern
    for (int i = 0; i < message.length(); i++) {
        rail[row][i] = message[i];  // Fill the current rail

        if (row == 0 || row == key - 1)
            down = !down;  // Change direction when we reach the top or bottom rail

        row += down ? 1 : -1;  // Move downwards or upwards
    }

    // Read the message by concatenating the rows
    std::string encrypted = "";
    for (int i = 0; i < key; i++) {
        for (int j = 0; j < message.length(); j++) {
            if (rail[i][j] != '\n') {
                encrypted += rail[i][j];
            }
        }
    }

    return encrypted;
}

// Rail Fence Cipher decryption
std::string rail_fence_decrypt(const std::string &message, int key) {
    if (key <= 1) return message;  // No decryption needed for 1 or less rails

    // Create a 2D array to store the rails
    std::vector<std::vector<char>> rail(key, std::vector<char>(message.length(), '\n'));
    int row = 0;
    bool down = false;  // Direction flag

    // Fill the rail array with placeholders to show the zigzag pattern
    for (int i = 0; i < message.length(); i++) {
        rail[row][i] = '*';  // Placeholder character

        if (row == 0 || row == key - 1)
            down = !down;  // Change direction when we reach the top or bottom rail

        row += down ? 1 : -1;  // Move downwards or upwards
    }

    // Fill the rails with the characters from the encrypted message
    int idx = 0;
    for (int i = 0; i < key; i++) {
        for (int j = 0; j < message.length(); j++) {
            if (rail[i][j] == '*') {
                rail[i][j] = message[idx++];
            }
        }
    }

    // Read the rails to decrypt the message
    std::string decrypted = "";
    row = 0;
    down = false;

    for (int i = 0; i < message.length(); i++) {
        decrypted += rail[row][i];

        if (row == 0 || row == key - 1)
            down = !down;  // Change direction when we reach the top or bottom rail

        row += down ? 1 : -1;  // Move downwards or upwards
    }

    return decrypted;
}
