#ifndef DIFFIE_HELLMAN_MITM_H
#define DIFFIE_HELLMAN_MITM_H

#include <iostream>
#include <cmath>
#include <string>

using namespace std;

class DiffieHellmanMITM {
public:
    long long modexp(long long base, long long exp, long long mod);
    long long bruteForce(long long g, long long p, long long publicKey, const string& victim);
    void simulate(long long g, long long p, long long A_pub, long long B_pub);
};

#endif // DIFFIE_HELLMAN_MITM_H
