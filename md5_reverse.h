#ifndef MD5_REVERSE_H
#define MD5_REVERSE_H

#include <string>

void openDCodeWithHash(const std::string& hash);
std::string searchWordlist(const std::string& hash, const std::string& wordlistPath);

#endif