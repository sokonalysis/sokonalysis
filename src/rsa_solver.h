#ifndef RSA_SOLVER_H
#define RSA_SOLVER_H

#include <gmpxx.h>
#include <string>

class RSASolver {
public:
    void inputPQ(const mpz_class& p, const mpz_class& q);
    void inputPN(const mpz_class& p, const mpz_class& n);
    void inputQN(const mpz_class& q, const mpz_class& n);
    void inputN(const mpz_class& n); // Optional: just to hold a value

    void solve();

    mpz_class getP() const;
    mpz_class getQ() const;
    mpz_class getN() const;
    mpz_class getPhi() const;
    mpz_class getE() const;
    mpz_class getD() const;

private:
    mpz_class p, q, n, phi, e, d;
    bool has_p = false, has_q = false, has_n = false;

    void computeMissingPQ();
    void computeKeys();
};

#endif
