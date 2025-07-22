#include "rsa_solver_common_n.h"
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

void RSASolverCommonN::get_mpz_input(const std::string& label, mpz_class& var) {
    std::string input;
    std::cout << YELLOW << "[>]" << RESET << " Enter " << label << ": ";
    std::getline(std::cin, input);
    var.set_str(input, 10);
}

void RSASolverCommonN::read_user_input() {
    get_mpz_input("modulus N", N);
    get_mpz_input("private exponent d", d);
    get_mpz_input("ciphertext", cipher);

    std::string e_str;
    std::cout << YELLOW << "[>]" << RESET << " Enter public exponent e (used to recover φ, default is 65537): ";
    std::getline(std::cin, e_str);
    e = e_str.empty() ? 65537 : mpz_class(e_str);

    int count = 0;
    std::cout << YELLOW << "[>]" << RESET << " How many small e_i values? ";
    std::string count_str;
    std::getline(std::cin, count_str);
    count = std::stoi(count_str);

    for (int i = 0; i < count; ++i) {
        std::cout << YELLOW << "[>]" << RESET << " Enter e_" << i + 1 << ": ";
        std::string ei_str;
        std::getline(std::cin, ei_str);
        mpz_class ei(ei_str);
        keys.emplace_back(N, ei);
    }
}

bool RSASolverCommonN::compute_phi() {
    mpz_class ed_minus_1 = e * d - 1;
    for (mpz_class k = 1; k < 10000000; ++k) {
        if (ed_minus_1 % k == 0) {
            mpz_class phi_candidate = ed_minus_1 / k;
            mpz_class g;
            mpz_gcd(g.get_mpz_t(), e.get_mpz_t(), phi_candidate.get_mpz_t());
            if (phi_candidate < N && g == 1) {
                phi = phi_candidate;
                std::cout << GREEN << "[-]" << RESET << " Found phi with k = " << k << std::endl;
                return true;
            }
        }
    }
    std::cerr << RED << "[x]" << RESET << " Could not find phi" << std::endl;
    return false;
}

mpz_class RSASolverCommonN::compute_combined_exponent() {
    mpz_class E = 1;
    for (const auto& key : keys) {
        E *= key.second;
    }
    return E;
}

mpz_class RSASolverCommonN::decrypt_message() {
    mpz_class E = compute_combined_exponent();
    mpz_invert(D.get_mpz_t(), E.get_mpz_t(), phi.get_mpz_t());
    mpz_powm(m.get_mpz_t(), cipher.get_mpz_t(), D.get_mpz_t(), N.get_mpz_t());
    return m;
}

std::string RSASolverCommonN::get_flag() {
    std::string flag_str;
    mpz_class temp = m;
    while (temp > 0) {
        flag_str.insert(flag_str.begin(), static_cast<char>(mpz_class(temp % 256).get_ui()));
        temp /= 256;
    }
    return flag_str;
}
