#ifndef POLLARD_SOLVER_H
#define POLLARD_SOLVER_H

#include <gmpxx.h>
#include <string>

class PollardSolve {
public:
    PollardSolve(const mpz_class& x, const mpz_class& n, const mpz_class& c, const mpz_class& e);
    std::string decryptFlag();

private:
    mpz_class x, n, c, e, p, q, m, d, decrypted;

    void computePQ();
    void computePrivateExponent();
    void decrypt();
};

#endif // POLLARD_SOLVER_H
