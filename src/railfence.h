#ifndef RAILFENCE_H
#define RAILFENCE_H

#include <string>

std::string rail_fence_encrypt(const std::string &message, int key);
std::string rail_fence_decrypt(const std::string &message, int key);

#endif // RAILFENCE_H
