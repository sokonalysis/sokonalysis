// vigenere.cpp
#include "vigenere.h"
#include <iostream>
#include <string>
#include <cctype>

using namespace std;

// Function to encrypt a message using the Vigenère Cipher
std::string vigenere_encrypt(std::string plaintext, std::string keyword) {
    string ciphertext = "";
    int key_index = 0;

    // Loop through the plaintext and apply Vigenère encryption
    for (int i = 0; i < plaintext.length(); i++) {
        char current_char = plaintext[i];
        if (isalpha(current_char)) {
            // Ensure the character is uppercase
            current_char = toupper(current_char);

            // Get the shift value from the keyword
            char key_char = toupper(keyword[key_index % keyword.length()]);
            int shift = key_char - 'A'; // A = 0, B = 1, ..., Z = 25

            // Encrypt the character by shifting it
            char encrypted_char = (current_char - 'A' + shift) % 26 + 'A';

            // Add the encrypted character to the ciphertext
            ciphertext += encrypted_char;

            // Move to the next character of the keyword
            key_index++;
        } else {
            // If the character is not a letter, keep it unchanged
            ciphertext += current_char;
        }
    }

    return ciphertext;
}

// Function to decrypt a message using the Vigenère Cipher
std::string vigenere_decrypt(std::string ciphertext, std::string keyword) {
    string plaintext = "";
    int key_index = 0;

    // Loop through the ciphertext and apply Vigenère decryption
    for (int i = 0; i < ciphertext.length(); i++) {
        char current_char = ciphertext[i];
        if (isalpha(current_char)) {
            // Ensure the character is uppercase
            current_char = toupper(current_char);

            // Get the shift value from the keyword
            char key_char = toupper(keyword[key_index % keyword.length()]);
            int shift = key_char - 'A'; // A = 0, B = 1, ..., Z = 25

            // Decrypt the character by subtracting the shift
            char decrypted_char = (current_char - 'A' - shift + 26) % 26 + 'A';

            // Add the decrypted character to the plaintext
            plaintext += decrypted_char;

            // Move to the next character of the keyword
            key_index++;
        } else {
            // If the character is not a letter, keep it unchanged
            plaintext += current_char;
        }
    }

    return plaintext;
}
