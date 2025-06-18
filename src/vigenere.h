// vigenere.h
#ifndef VIGENERE_H
#define VIGENERE_H

#include <string>

// Function to encrypt a message using the Vigenère Cipher
std::string vigenere_encrypt(std::string plaintext, std::string keyword);

// Function to decrypt a message using the Vigenère Cipher
std::string vigenere_decrypt(std::string ciphertext, std::string keyword);

#endif // VIGENERE_H
