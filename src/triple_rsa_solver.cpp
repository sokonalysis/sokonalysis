#include "triple_rsa_solver.h"
#include <iostream>
#include <gmpxx.h>
#include <string>

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

void solveTripleRSA() {
    size_t count;
    std::cout << YELLOW << "[>]" << RESET << " Enter number of n values to input (e.g. 3): ";
    std::cin >> count;

    std::vector<mpz_class> n(count);
    for (size_t i = 0; i < count; ++i) {
        std::cout << YELLOW << "[>]" << RESET << " Enter n" << (i+1) << ": ";
        std::cin >> n[i];
    }

    mpz_class e;
    std::cout << YELLOW << "[>]" << RESET << " Enter e: ";
    std::cin >> e;
    mpz_class c;
    std::cout << YELLOW << "[>]" << RESET << " Enter ciphertext c: ";
    std::cin >> c;

    // Compute pairwise gcds
    mpz_class p = gcd(n[0], n[1]);
    mpz_class q = gcd(n[0], n[2]);
    mpz_class r = gcd(n[1], n[2]);

    // Compute phi for each key
    mpz_class phi1 = (p - 1) * (q - 1);
    mpz_class phi2 = (p - 1) * (r - 1);
    mpz_class phi3 = (q - 1) * (r - 1);

    // Compute private exponents
    mpz_class d1 = mpz_class();
    mpz_invert(d1.get_mpz_t(), e.get_mpz_t(), phi1.get_mpz_t());

    mpz_class d2 = mpz_class();
    mpz_invert(d2.get_mpz_t(), e.get_mpz_t(), phi2.get_mpz_t());

    mpz_class d3 = mpz_class();
    mpz_invert(d3.get_mpz_t(), e.get_mpz_t(), phi3.get_mpz_t());

    std::vector<std::pair<mpz_class, mpz_class>> keys = {
        {d3, n[2]}, {d2, n[1]}, {d1, n[0]}
    };

    // Decrypt step by step
    for (const auto& [d, nval] : keys) {
        mpz_powm(c.get_mpz_t(), c.get_mpz_t(), d.get_mpz_t(), nval.get_mpz_t());
    }

    // Convert result to string
    std::string plaintext;
    plaintext.resize(mpz_sizeinbase(c.get_mpz_t(), 256));
    mpz_export(&plaintext[0], nullptr, 1, 1, 0, 0, c.get_mpz_t());

    std::cout << BLUE << "_________________________________________________________________\n" << RESET;
    std::cout << std::endl;
    std::cout << GREEN << "[-]" << RESET << " Decrypted message: " << GREEN << plaintext << RESET << std::endl;
    std::cout << BLUE << "_________________________________________________________________\n" << RESET;
}
