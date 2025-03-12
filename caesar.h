#ifndef CAESAR_H
#define CAESAR_H

#include <string>

// Declare the caesar_decrypt function here so it can be used in other files
std::string caesar_encrypt(const std::string& message, int shift, int mapping);
std::string caesar_decrypt(const std::string& message, int shift, int mapping);  // Declaration

#endif // CAESAR_H
