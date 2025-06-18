#include "pollard.h"
#include <iostream>
#include <sstream>

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

PollardSolver::PollardSolver(const std::string& hex_n, const std::string& hex_c) {
    n.set_str(hex_n, 16);
    c.set_str(hex_c, 16);
    e = 65537;
}

mpz_class PollardSolver::gcdPollard(const mpz_class& a, const mpz_class& n, unsigned int B) {
    mpz_class M = 1;
    for (unsigned int i = 2; i <= B; ++i) {
        M *= i;
    }

    mpz_class aM;
    mpz_powm(aM.get_mpz_t(), a.get_mpz_t(), M.get_mpz_t(), n.get_mpz_t());
    aM -= 1;

    mpz_class g;
    mpz_gcd(g.get_mpz_t(), aM.get_mpz_t(), n.get_mpz_t());

    return g;
}

bool PollardSolver::factorize() {
    mpz_class a = 2;
    unsigned int B = 65535;

    while (true) {
        mpz_class g = gcdPollard(a, n, B);

        if (g == 1) {
            ++B;
        } else if (g == n) {
            --B;
        } else {
            p = g;
            q = n / p;

            std::cout << BLUE << "_________________________________________________________________\n" << RESET;
            std::cout << std::endl;
            std::cout << GREEN << "[-]" << RESET << " p factor : " << GREEN << p.get_str() << RESET << std::endl;
            std::cout << GREEN << "[-]" << RESET << " q factor : " << GREEN << q.get_str() << RESET << std::endl;
            std::cout << BLUE << "_________________________________________________________________\n" << RESET;

            mpz_class phi = computePhi(p, q);
            if (mpz_invert(d.get_mpz_t(), e.get_mpz_t(), phi.get_mpz_t()) == 0) {
                std::cout << BLUE << "_________________________________________________________________\n" << RESET;
                std::cout << std::endl;
                std::cerr << "[x] Modular inverse failed." << std::endl;
                std::cout << BLUE << "_________________________________________________________________\n" << RESET;
                return false;
            }
            return true;
        }
    }
}

mpz_class PollardSolver::computePhi(const mpz_class& p, const mpz_class& q) {
    return (p - 1) * (q - 1);
}

std::string PollardSolver::mpzToStr(const mpz_class& m) {
    std::string hexStr = m.get_str(16);
    if (hexStr.size() % 2 != 0) {
        hexStr = "0" + hexStr;
    }

    std::string result;
    for (size_t i = 0; i < hexStr.length(); i += 2) {
        std::string byte = hexStr.substr(i, 2);
        char chr = static_cast<char>(std::stoul(byte, nullptr, 16));
        result.push_back(chr);
    }
    return result;
}

std::string PollardSolver::getFlag() {
    mpz_class m;
    mpz_powm(m.get_mpz_t(), c.get_mpz_t(), d.get_mpz_t(), n.get_mpz_t()); // m = c^d mod n
    return mpzToStr(m);
}
