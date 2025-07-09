#ifndef SHA1_EASY_H
#define SHA1_EASY_H

#include <string>

std::string sha1(const std::string& input);
std::string searchSHA1Wordlist(const std::string& hash, const std::string& wordlistPath);
void openSHA1OnlineLookup(const std::string& hash);

#endif // SHA1_EASY_H
