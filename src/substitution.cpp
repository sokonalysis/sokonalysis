#include "substitution.h"
#include <iostream>
#include <algorithm>
#include <cctype>
#include <map>
#include <vector>

// Set colors
#define GREEN   "\033[32m"
#define CYAN    "\033[36m"
#define BLUE    "\033[34m"
#define MAGENTA "\033[35m"
#define YELLOW  "\033[33m"
#define WHITE   "\033[37m"
#define RED     "\033[31m"
#define ORANGE "\033[38;5;208m"
#define BOLD    "\033[1m"
#define CLEAR   "\033[2J\033[H"  // Clears screen and moves cursor to top-left
#define RESET   "\033[0m"

SubstitutionCipher::SubstitutionCipher() {}

void SubstitutionCipher::setKey(const std::string& k) {
    key = k;
    buildMaps();
}

void SubstitutionCipher::buildMaps() {
    encMap.clear();
    decMap.clear();
    std::string alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    for (int i = 0; i < 26; ++i) {
        char plain = alphabet[i];
        char sub = std::toupper(key[i]);
        encMap[plain] = sub;
        decMap[sub] = plain;
    }
}

std::string SubstitutionCipher::encrypt(const std::string& plaintext) {
    std::string result;
    for (char ch : plaintext) {
        if (std::isalpha(ch)) {
            char upper = std::toupper(ch);
            result += std::isupper(ch) ? encMap[upper] : std::tolower(encMap[upper]);
        } else {
            result += ch;
        }
    }
    return result;
}

std::string SubstitutionCipher::decrypt(const std::string& ciphertext) {
    std::string result;
    for (char ch : ciphertext) {
        if (std::isalpha(ch)) {
            char upper = std::toupper(ch);
            result += std::isupper(ch) ? decMap[upper] : std::tolower(decMap[upper]);
        } else {
            result += ch;
        }
    }
    return result;
}