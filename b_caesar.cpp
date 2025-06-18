#include "b_caesar.h"
#include "caesar.h"  // Include caesar.h to access caesar_decrypt
#include <vector>
#include <cctype>  // For isalpha

// Function to brute-force decrypt the Caesar cipher by trying all possible shifts (1 to 25)
std::vector<std::string> brute_force_caesar_decrypt(const std::string& encrypted_message, int mapping) {
    std::vector<std::string> possible_decryptions;

    // Try every possible shift from 1 to 25
    for (int shift = 1; shift < 26; shift++) {
        std::string decrypted_message = caesar_decrypt(encrypted_message, shift, mapping);
        possible_decryptions.push_back(decrypted_message);
    }

    return possible_decryptions;
}
