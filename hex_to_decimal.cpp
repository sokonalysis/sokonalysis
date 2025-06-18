#include "hex_to_decimal.h"
#include <iostream>
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

void convert_hex_to_decimal() {
    std::string hex_str;
    std::cout << YELLOW << "[>]" << RESET << " Enter hexadecimal (e.g. 0xABC123): ";
    std::getline(std::cin, hex_str);

    if (hex_str.empty()) {
        std::cout << BLUE << "_________________________________________________________________\n" << RESET;
        std::cout << std::endl;
        std::cout << RED << "[!]" << RESET << " Empty input.\n";
        std::cout << BLUE << "_________________________________________________________________\n" << RESET;
        return;
    }

    // Remove optional 0x prefix
    if (hex_str.substr(0, 2) == "0x" || hex_str.substr(0, 2) == "0X") {
        hex_str = hex_str.substr(2);
    }

    std::transform(hex_str.begin(), hex_str.end(), hex_str.begin(), ::tolower);

    mpz_class decimal;
    try {
        decimal.set_str(hex_str, 16); // base 16
        std::cout << BLUE << "_________________________________________________________________\n" << RESET;
        std::cout << std::endl;
        std::cout << RED << "[+]" << RESET << " Decimal: " << RED << decimal.get_str() << RESET << std::endl;
        std::cout << BLUE << "_________________________________________________________________\n" << RESET;
    } catch (...) {
        std::cout << BLUE << "_________________________________________________________________\n" << RESET;
        std::cout << std::endl;
        std::cout << RED << "[!]" << RESET << " Invalid hexadecimal input.\n";
        std::cout << BLUE << "_________________________________________________________________\n" << RESET;
    }
}
