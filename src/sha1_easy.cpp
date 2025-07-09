#include "sha1_easy.h"
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

std::string sha1(const std::string& input) {
    CryptoPP::SHA1 hash;
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

std::string searchSHA1Wordlist(const std::string& hash, const std::string& wordlistPath) {
    std::ifstream file(wordlistPath);
    if (!file.is_open()) {
        return "Failed to open wordlist.";
    }

    std::string line;
    std::string cleaned;
    std::string targetHash = toLower(hash);

    while (getline(file, line)) {
        cleaned = cleanLine(line);
        std::string wordHash = toLower(sha1(cleaned));

        if (wordHash == targetHash) {
            return cleaned;
        }
    }

    return "No match found in wordlist.";
}

void openSHA1OnlineLookup(const std::string& hash) {
    std::string url = "https://sha1.gromweb.com/?hash=" + hash;
    std::string command = std::string(OPEN_COMMAND) + url + "\"";
    system(command.c_str());
}
