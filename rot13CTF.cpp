#include "rot13CTF.h"

char rot13Char(char c) {
    if ('A' <= c && c <= 'Z') return ((c - 'A' + 13) % 26) + 'A';
    if ('a' <= c && c <= 'z') return ((c - 'a' + 13) % 26) + 'a';
    return c;
}

std::string applyROT13(const std::string& input) {
    std::string result;
    result.reserve(input.size());
    for (char c : input) {
        result += rot13Char(c);
    }
    return result;
}
