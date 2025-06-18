#include "MiniRSA.h"
#include <iostream>
#include <gmpxx.h>
#include <cctype>

MiniRSA::MiniRSA(const std::string& N_str, const std::string& e_str, const std::string& c_str)
    : N_str(N_str), e_str(e_str), c_str(c_str) {}

std::string MiniRSA::decrypt() {
    mpz_class N(N_str), c(c_str);
    int e = std::stoi(e_str);

    for (int i = 0; i < 4000; ++i) {
        mpz_class test = i * N + c;
        mpz_class root;

        // Integer e-th root: root = (test)^(1/e)
        mpz_root(root.get_mpz_t(), test.get_mpz_t(), e);

        // Convert to string
        std::string result;
        mpz_class temp = root;
        while (temp > 0) {
            char byte = static_cast<char>(mpz_class(temp % 256).get_si());
            result.insert(result.begin(), byte);
            temp /= 256;
        }

        // Basic ASCII printability check
        bool isReadable = true;
        for (char ch : result) {
            if (!isprint(static_cast<unsigned char>(ch)) && ch != '\n') {
                isReadable = false;
                break;
            }
        }

        if (isReadable && !result.empty()) {
            return result;  // First clean result found
        }
    }

    return "No readable plaintext found.";
}
