#include "sha1_easy.h"
#include <cryptopp/sha.h>
#include <cryptopp/hex.h>
#include <cryptopp/filters.h>
#include <fstream>
#include <cstdlib> // for system()
#include <string>

#ifdef _WIN32
    #define OPEN_COMMAND "start "
#elif __APPLE__
    #define OPEN_COMMAND "open "
#else
    #define OPEN_COMMAND "xdg-open "
#endif

// Compute SHA-1 hash
std::string sha1(const std::string& input) {
    CryptoPP::SHA1 hash;
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

// Search for SHA-1 hash in local wordlist
std::string searchSHA1Wordlist(const std::string& hash, const std::string& wordlistPath) {
    std::ifstream file(wordlistPath);
    if (!file.is_open()) {
        return "Failed to open wordlist.";
    }

    std::string word;
    while (getline(file, word)) {
        if (sha1(word) == hash) {
            return word;
        }
    }

    return "No match found in wordlist.";
}

// Open online SHA-1 reverser in browser
void openSHA1OnlineLookup(const std::string& hash) {
    std::string url = "https://sha1.gromweb.com/?hash=" + hash;  // Include the hash as a fragment
#ifdef _WIN32
    std::string command = "start \"\" \"" + url + "\"";  // Empty title is required on Windows
#elif __APPLE__
    std::string command = "open \"" + url + "\"";
#else
    std::string command = "xdg-open \"" + url + "\"";
#endif
    system(command.c_str());
}

