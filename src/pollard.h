#ifndef POLLARD_H
#define POLLARD_H

#include <gmpxx.h>
#include <string>

class PollardSolver {
public:
    PollardSolver(const std::string& hex_n, const std::string& hex_c);
    bool factorize();
    std::string getFlag();

private:
    mpz_class n, c, p, q, d, e;
    mpz_class gcdPollard(const mpz_class& a, const mpz_class& n, unsigned int B);
    mpz_class computePhi(const mpz_class& p, const mpz_class& q);
    std::string mpzToStr(const mpz_class& m);
};

#endif
