#ifndef SHA256_EASY_H
#define SHA256_EASY_H

#include <string>

std::string sha256(const std::string& input);
std::string searchSHA256Wordlist(const std::string& hash, const std::string& wordlistPath);
void openSHA256OnlineLookup(const std::string& hash);

#endif // SHA256_EASY_H
