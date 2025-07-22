#ifndef MOD_SOLVER_H
#define MOD_SOLVER_H

#include <vector>
#include <gmpxx.h>
#include <string>

class ModSolver {
public:
    void read_user_input();
    void solve();
    std::string get_flag() const;

private:
    struct Equation {
        mpz_class a, m, b;
    };
    std::vector<Equation> equations;
    std::vector<mpz_class> solutions;
    std::string flag;

    void get_mpz_input(const std::string& label, mpz_class& var);
};

#endif // MOD_SOLVER_H
