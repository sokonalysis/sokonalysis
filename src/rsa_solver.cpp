#include "rsa_solver.h"
#include <iostream>

void RSASolver::inputPQ(const mpz_class& p_val, const mpz_class& q_val) {
    p = p_val;
    q = q_val;
    has_p = has_q = true;
    n = p * q;
    has_n = true;
}

void RSASolver::inputPN(const mpz_class& p_val, const mpz_class& n_val) {
    p = p_val;
    has_p = true;
    n = n_val;
    has_n = true;
}

void RSASolver::inputQN(const mpz_class& q_val, const mpz_class& n_val) {
    q = q_val;
    has_q = true;
    n = n_val;
    has_n = true;
}

void RSASolver::inputN(const mpz_class& n_val) {
    n = n_val;
    has_n = true;
}

void RSASolver::computeMissingPQ() {
    if (has_p && has_n && !has_q) {
        if (n % p == 0) {
            q = n / p;
            has_q = true;
        }
    } else if (has_q && has_n && !has_p) {
        if (n % q == 0) {
            p = n / q;
            has_p = true;
        }
    } else if (has_n && !has_p && !has_q) {
        // Attempt factoring n
        mpz_class factor = 2, rem;
        while (factor * factor <= n) {
            mpz_mod(rem.get_mpz_t(), n.get_mpz_t(), factor.get_mpz_t());
            if (rem == 0) {
                p = factor;
                q = n / factor;
                has_p = has_q = true;
                break;
            }
            factor++;
        }
    }
}


void RSASolver::computeKeys() {
    if (has_p && has_q) {
        phi = (p - 1) * (q - 1);
        e = 65537;
        if (!mpz_invert(d.get_mpz_t(), e.get_mpz_t(), phi.get_mpz_t())) {
            std::cerr << "[!] Failed to compute modular inverse (d)." << std::endl;
        }
    }
}

void RSASolver::solve() {
    computeMissingPQ();
    computeKeys();
}

mpz_class RSASolver::getP() const { return p; }
mpz_class RSASolver::getQ() const { return q; }
mpz_class RSASolver::getN() const { return n; }
mpz_class RSASolver::getPhi() const { return phi; }
mpz_class RSASolver::getE() const { return e; }
mpz_class RSASolver::getD() const { return d; }
