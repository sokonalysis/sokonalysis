#ifndef RSA_SOLVER_COMMON_N_H
#define RSA_SOLVER_COMMON_N_H

#include <vector>
#include <utility>
#include <string>
#include <gmpxx.h>

class RSASolverCommonN {
public:
    void read_user_input();
    bool compute_phi();
    mpz_class compute_combined_exponent();
    mpz_class decrypt_message();
    std::string get_flag();

private:
    mpz_class N, d, cipher, phi, e, D, m;
    std::vector<std::pair<mpz_class, mpz_class>> keys;
    void get_mpz_input(const std::string& label, mpz_class& var);
};

#endif // RSA_SOLVER_COMMON_N_H
