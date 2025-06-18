#ifndef SHA256_EASY_H
#define SHA256_EASY_H

#include <string>

// Generate SHA-256 hash from input string
std::string sha256(const std::string& input);

// Search a wordlist file for a string that matches the given SHA-256 hash
std::string searchSHA256Wordlist(const std::string& hash, const std::string& wordlistPath);

// Open an online reverse lookup site in the default browser
void openSHA256OnlineLookup(const std::string& hash);

#endif // SHA256_EASY_H
