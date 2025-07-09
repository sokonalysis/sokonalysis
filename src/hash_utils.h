#ifndef HASH_UTILS_H
#define HASH_UTILS_H

#include <string>

// Remove trailing carriage return if present
std::string cleanLine(const std::string& line);

// Convert string to lowercase
std::string toLower(const std::string& input);

#endif // HASH_UTILS_H
