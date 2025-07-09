#include "sha256_easy.h"
#include "hash_utils.h"

#include <cryptopp/sha.h>
#include <cryptopp/hex.h>
#include <cryptopp/filters.h>
#include <fstream>
#include <cstdlib>
#include <string>

#ifdef _WIN32
    #define OPEN_COMMAND "start \"\" \""
#elif __APPLE__
    #define OPEN_COMMAND "open \""
#else
    #define OPEN_COMMAND "xdg-open \""
#endif

std::string sha256(const std::string& input) {
    CryptoPP::SHA256 hash;
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

std::string searchSHA256Wordlist(const std::string& hash, const std::string& wordlistPath) {
    std::ifstream file(wordlistPath);
    if (!file.is_open()) {
        return "Failed to open wordlist.";
    }

    std::string word;
    std::string cleaned;
    std::string targetHash = toLower(hash);

    while (getline(file, word)) {
        cleaned = cleanLine(word);
        std::string wordHash = toLower(sha256(cleaned));

        if (wordHash == targetHash) {
            return cleaned;
        }
    }

    return "No match found in wordlist.";
}

void openSHA256OnlineLookup(const std::string& hash) {
    std::string url = "https://md5hashing.net/hash/sha256/" + hash;
    std::string command = std::string(OPEN_COMMAND) + url + "\"";
    system(command.c_str());
}
