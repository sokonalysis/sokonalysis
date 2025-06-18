// caesar_polyalphabetic.h
#ifndef CAESAR_POLYALPHABETIC_H
#define CAESAR_POLYALPHABETIC_H

#include <string>

// Function to encrypt the message using Caesar Polyalphabetic Cipher
std::string caesar_polyalphabetic_encrypt(const std::string& message, const std::string& keyword, int mapping);

// Function to decrypt the message using Caesar Polyalphabetic Cipher
std::string caesar_polyalphabetic_decrypt(const std::string& message, const std::string& keyword, int mapping);

#endif // CAESAR_POLYALPHABETIC_H
