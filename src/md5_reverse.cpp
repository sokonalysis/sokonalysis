#define CRYPTOPP_ENABLE_NAMESPACE_WEAK 1

#include "md5_reverse.h"
#include "hash_utils.h"

#include <iostream>
#include <fstream>
#include <string>
#include <cstdlib>

#include <cryptopp/md5.h>
#include <cryptopp/hex.h>
#include <cryptopp/filters.h>

#if defined(_WIN32) || defined(_WIN64)
    #define OPEN_COMMAND "start \"\" \""
#elif defined(__APPLE__)
    #define OPEN_COMMAND "open \""
#else
    #define OPEN_COMMAND "xdg-open \""
#endif

void openDCodeWithHash(const std::string& hash) {
    std::string url = "https://md5hashing.net/hash/md5/" + hash;
    std::string command = std::string(OPEN_COMMAND) + url + "\"";
    system(command.c_str());
}

std::string md5(const std::string& input) {
    CryptoPP::Weak::MD5 hash;
    std::string digest;

    CryptoPP::StringSource ss(input, true,
        new CryptoPP::HashFilter(hash,
            new CryptoPP::HexEncoder(
                new CryptoPP::StringSink(digest), false
            )
        )
    );

    return digest;
}

std::string searchWordlist(const std::string& hash, const std::string& wordlistPath) {
    std::ifstream file(wordlistPath);
    if (!file.is_open()) {
        return "Failed to open wordlist.";
    }

    std::string word;
    std::string cleaned;
    std::string targetHash = toLower(hash);

    while (getline(file, word)) {
        cleaned = cleanLine(word);
        std::string wordHash = toLower(md5(cleaned));

        if (wordHash == targetHash) {
            return cleaned;
        }
    }

    return "No match found in wordlist.";
}
