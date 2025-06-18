#include "PollardSolver.h"
#include <sstream>
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

PollardSolve::PollardSolve(const mpz_class& x, const mpz_class& n, const mpz_class& c, const mpz_class& e)
    : x(x), n(n), c(c), e(e) {
    computePQ();
    computePrivateExponent();
    decrypt();
}

void PollardSolve::computePQ() {
    std::cout << std::endl;
    std::cout << RED << "[+]" << RESET << " Computing p and q from x and n..." << std::endl;
    mpz_class sqrt_term;
    mpz_class temp = x * x - 4 * n;
    mpz_sqrt(sqrt_term.get_mpz_t(), temp.get_mpz_t());

    p = (x + sqrt_term) / 2;
    q = n / p;

    std::cout << BLUE << "_________________________________________________________________\n" << RESET;
    std::cout << std::endl;
    std::cout << GREEN << "[-]" << RESET << "  p = " << GREEN << p.get_str(16) << RESET << std::endl;
    std::cout << GREEN << "[-]" << RESET << "  q = " << GREEN << q.get_str(16) << RESET << std::endl;
    std::cout << BLUE << "_________________________________________________________________\n" << RESET;
}

void PollardSolve::computePrivateExponent() {
    std::cout << std::endl;
    std::cout << RED << "[+]" << RESET << " Computing private exponent d..." << std::endl;
    mpz_class p1 = p - 1;
    mpz_class q1 = q - 1;
    mpz_lcm(m.get_mpz_t(), p1.get_mpz_t(), q1.get_mpz_t());
    mpz_invert(d.get_mpz_t(), e.get_mpz_t(), m.get_mpz_t());
    std::cout << BLUE << "_________________________________________________________________\n" << RESET;
    std::cout << std::endl;
    std::cout << GREEN << "[-]" << RESET << "  d = " << GREEN << d.get_str(16) << RESET << std::endl;
    std::cout << BLUE << "_________________________________________________________________\n" << RESET;
}

void PollardSolve::decrypt() {
    std::cout << std::endl;
    std::cout << GREEN << "[-]" << RESET << " Decrypting ciphertext..." << std::endl;
    mpz_powm(decrypted.get_mpz_t(), c.get_mpz_t(), d.get_mpz_t(), n.get_mpz_t());
    std::cout << BLUE << "_________________________________________________________________\n" << RESET;
    std::cout << std::endl;
    std::cout << GREEN << "[-]" << RESET << "  Decrypted hex = " << GREEN << decrypted.get_str(16) << RESET <<  std::endl;
    std::cout << BLUE << "_________________________________________________________________\n" << RESET;
}

std::string PollardSolve::decryptFlag() {
    std::stringstream ss;
    ss << std::hex << decrypted;
    std::string hex_str = ss.str();

    if (hex_str.size() % 2 != 0) {
        hex_str = "0" + hex_str;
    }

    std::string flag;
    for (size_t i = 0; i < hex_str.size(); i += 2) {
        std::string byte = hex_str.substr(i, 2);
        flag += static_cast<char>(std::stoi(byte, nullptr, 16));
    }

    return flag;
}
