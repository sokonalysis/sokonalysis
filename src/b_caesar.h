#ifndef B_CAESAR_H
#define B_CAESAR_H

#include <string>
#include <vector>

// Function to brute-force decrypt the Caesar cipher (trying all shifts)
std::vector<std::string> brute_force_caesar_decrypt(const std::string& encrypted_message, int mapping);

#endif // B_CAESAR_H
