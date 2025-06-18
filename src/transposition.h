#ifndef TRANSPOSITION_H
#define TRANSPOSITION_H

#include <string>

std::string transposition_encrypt(const std::string& message, int key);
std::string transposition_decrypt(const std::string& message, int key);

#endif // TRANSPOSITION_H
