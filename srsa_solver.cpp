#include "srsa_solver.h"
#include <iostream>

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

std::string mpz_to_ascii(mpz_class m) {
    std::string result;
    while (m > 0) {
        mpz_class rem = m % 256;
        char ch = static_cast<char>(rem.get_ui());
        result = ch + result;
        m /= 256;
    }
    return result;
}

void solve_srsa() {
    mpz_class n, e, ct;
    std::cout << YELLOW << "[>]" << RESET << " Enter n: ";
    std::cin >> n;
    std::cout << YELLOW << "[>]" << RESET << " Enter e: ";
    std::cin >> e;
    std::cout << YELLOW << "[>]" << RESET << " Enter ct: ";
    std::cin >> ct;

    mpz_class original_ct = ct;
    mpz_class i;
    for (i = 0; i < e; ++i) {
        mpz_class pt = ct / e;
        std::string decoded = mpz_to_ascii(pt);

        if (decoded.find("rar") == 0 || decoded.find("ctf") != std::string::npos || decoded.find("flag") != std::string::npos) {
            std::cout << BLUE << "_________________________________________________________________\n" << RESET;
            std::cout << std::endl;
            std::cout << GREEN << "[-]" << RESET << " Decrypted message found after " << i.get_str() << " iterations: " << GREEN << decoded << RESET << std::endl;
            std::cout << BLUE << "_________________________________________________________________\n" << RESET;
            return;
        }

        ct += n;
    }
    std::cout << BLUE << "_________________________________________________________________\n" << RESET;
    std::cout << std::endl;
    std::cout << RED << "[x]" << RESET << " No valid message found after " << i.get_str() << " iterations.\n";
    std::cout << BLUE << "_________________________________________________________________\n" << RESET;
}
