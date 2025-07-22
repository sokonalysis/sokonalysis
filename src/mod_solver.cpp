#include "mod_solver.h"
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


void ModSolver::get_mpz_input(const std::string& label, mpz_class& var) {
    std::string input;
    std::cout << YELLOW << "[>]" << RESET << " Enter " << label << ": ";
    std::getline(std::cin, input);
    var.set_str(input, 10);
}

void ModSolver::read_user_input() {
    int count;
    std::string input;
    std::cout << YELLOW << "[>]" << RESET << " Enter the number of equations: ";
    std::getline(std::cin, input);
    count = std::stoi(input);

    for (int i = 0; i < count; ++i) {
        std::cout << GREEN << "Equation " << i + 1 << ":" << RESET << std::endl;
        mpz_class a, m, b;
        get_mpz_input("a", a);
        get_mpz_input("m (modulus)", m);
        get_mpz_input("b (result)", b);
        equations.push_back({a, m, b});
    }
}

void ModSolver::solve() {
    for (const auto& eq : equations) {
        mpz_class inv, x;
        if (mpz_invert(inv.get_mpz_t(), eq.a.get_mpz_t(), eq.m.get_mpz_t()) == 0) {
            std::cerr << RED << "[x]" << RESET << " No modular inverse exists for a = " << RED << eq.a << RESET << " mod " << RED << eq.m << RESET << "\n";
            solutions.push_back(0);
            flag += '?';
            continue;
        }

        x = (eq.b * inv) % eq.m;
        solutions.push_back(x);
        flag += static_cast<char>(x.get_ui() % 256);
    }
}

std::string ModSolver::get_flag() const {
    return flag;
}
