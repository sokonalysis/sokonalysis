#include "base64CTF.h"
#include <openssl/bio.h>
#include <openssl/evp.h>
#include <openssl/buffer.h>
#include <iostream>
#include <iomanip>
#include <string>
#include <cctype>
#include <stdexcept>
#include <algorithm>

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

namespace {

// Clean base64 input by removing whitespace (spaces, newlines, tabs)
std::string cleanBase64Input(const std::string& input) {
    std::string output;
    output.reserve(input.size());
    for (char c : input) {
        if (!std::isspace(static_cast<unsigned char>(c))) {
            output += c;
        }
    }
    return output;
}

// Check if a character is valid base64 character
bool isValidBase64Char(char c) {
    return (std::isalnum(static_cast<unsigned char>(c)) || c == '+' || c == '/' || c == '=');
}

// Validate entire input string (ignore whitespace)
bool validateBase64Input(const std::string& input) {
    for (char c : input) {
        if (std::isspace(static_cast<unsigned char>(c))) continue;
        if (!isValidBase64Char(c)) return false;
    }
    return true;
}

// Check if string is printable ASCII (including whitespace)
bool isPrintableASCII(const std::string& str) {
    for (unsigned char c : str)
        if (!std::isprint(c) && !std::isspace(c))
            return false;
    return true;
}

std::string decodeBase64(const std::string& cipher) {
    BIO* bio = BIO_new_mem_buf(cipher.data(), static_cast<int>(cipher.size()));
    BIO* b64 = BIO_new(BIO_f_base64());
    bio = BIO_push(b64, bio);

    BIO_set_flags(bio, BIO_FLAGS_BASE64_NO_NL);

    std::string decoded(cipher.size(), '\0');
    int decoded_len = BIO_read(bio, &decoded[0], static_cast<int>(cipher.size()));
    if (decoded_len <= 0) {
        BIO_free_all(bio);
        throw std::runtime_error("Failed to decode base64");
    }
    decoded.resize(decoded_len);
    BIO_free_all(bio);
    return decoded;
}

} // anonymous namespace

void decodeAndPrintBase64(const std::string& cipher) {
    if (!validateBase64Input(cipher)) {
        std::cout << BLUE << "_________________________________________________________________\n" << RESET;
        std::cout << std::endl;
        std::cerr << RED << "[x]" << RESET << " Input contains invalid base64 characters" << std::endl;
        std::cout << BLUE << "_________________________________________________________________\n" << RESET;
        return;
    }

    try {
        std::string cleanInput = cleanBase64Input(cipher);
        std::string decoded = decodeBase64(cleanInput);

        if (isPrintableASCII(decoded)) {
            std::cout << BLUE << "_________________________________________________________________\n" << RESET;
            std::cout << std::endl;
            std::cout << GREEN << "[-]" << RESET << " Decoded result: " << GREEN << decoded << RESET << std::endl;
            std::cout << BLUE << "_________________________________________________________________\n" << RESET;
        } else {
            std::cout << BLUE << "_________________________________________________________________\n" << RESET;
            std::cout << std::endl;
            std::cout << GREEN << "[-]" << RESET << " Decoded result (raw hex bytes):" << std::endl;
            std::cout << GREEN;
            for (unsigned char c : decoded) {
                std::cout << std::hex << std::uppercase << std::setw(2) << std::setfill('0')
                          << (int)c << " ";
            }
            std::cout << std::dec << std::endl;
            std::cout << RESET;
            std::cout << BLUE << "_________________________________________________________________\n" << RESET;
        }
    } catch (const std::exception& e) {
        std::cout << BLUE << "_________________________________________________________________\n" << RESET;
        std::cout << std::endl;
        std::cerr << RED << "[x]" << RESET << " Error decoding base64: " << RED << e.what() << RESET << std::endl;
        std::cout << BLUE << "_________________________________________________________________\n" << RESET;
    }
}
