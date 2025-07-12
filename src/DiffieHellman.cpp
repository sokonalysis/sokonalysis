// DiffieHellman.cpp

#include "DiffieHellman.h"

DiffieHellman::DiffieHellman(int base, int modulus, int privateKey)
    : g(base), p(modulus), secret(privateKey) {}

int DiffieHellman::generatePublicKey() {
    int result = 1;
    for (int i = 0; i < secret; ++i) {
        result = (result * g) % p;
    }
    return result;
}

int DiffieHellman::computeSharedKey(int receivedPublicKey) {
    int result = 1;
    for (int i = 0; i < secret; ++i) {
        result = (result * receivedPublicKey) % p;
    }
    return result;
}
