#include "hash_utils.h"
#include <algorithm>

std::string cleanLine(const std::string& line) {
    std::string result = line;
    if (!result.empty() && result.back() == '\r') {
        result.pop_back();
    }
    return result;
}

std::string toLower(const std::string& input) {
    std::string lower = input;
    std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);
    return lower;
}
