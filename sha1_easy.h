#pragma once
#include <string>

// Compute SHA-1 hash from a given input string
std::string sha1(const std::string& input);

// Search a local wordlist for a string matching the SHA-1 hash
std::string searchSHA1Wordlist(const std::string& hash, const std::string& wordlistPath);

// Open browser to reverse SHA-1 hash using online service
void openSHA1OnlineLookup(const std::string& hash);