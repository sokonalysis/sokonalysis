#define CRYPTOPP_ENABLE_NAMESPACE_WEAK 1

#include "md5_reverse.h"
#include <iostream>
#include <fstream>
#include <string>
#include <cstdlib> // for system()

#include <cryptopp/md5.h>
#include <cryptopp/hex.h>
#include <cryptopp/filters.h>

// Launch browser to online MD5 cracker
void openDCodeWithHash(const std::string& hash) {
    std::string url = "https://md5hashing.net/hash/md5/" + hash;
    std::string command = "start " + url; // Windows-specific
    system(command.c_str());
}

// Compute MD5 hash using Crypto++ (Weak::MD5)
std::string md5(const std::string& input) {
    CryptoPP::Weak::MD5 hash;
    std::string digest;

    CryptoPP::StringSource ss(input, true,
        new CryptoPP::HashFilter(hash,
            new CryptoPP::HexEncoder(
                new CryptoPP::StringSink(digest), false // lowercase
            )
        )
    );

    return digest;
}

// Search for a hash match in the given wordlist
std::string searchWordlist(const std::string& hash, const std::string& wordlistPath) {
    std::ifstream file(wordlistPath);
    if (!file.is_open()) {
        return "Failed to open wordlist.";
    }

    std::string word;
    while (getline(file, word)) {
        if (md5(word) == hash) {
            return word;
        }
    }

    return "No match found in wordlist.";
}
