#include "diffieHellmanMITM.h"

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

long long DiffieHellmanMITM::modexp(long long base, long long exp, long long mod) {
    long long result = 1;
    base %= mod;

    while (exp > 0) {
        if (exp % 2 == 1)
            result = (result * base) % mod;
        exp >>= 1;
        base = (base * base) % mod;
    }

    return result;
}

long long DiffieHellmanMITM::bruteForce(long long g, long long p, long long publicKey, const string& victim) {
    cout << endl;
    cout << GREEN << "   Brute Force Attempt to find " << victim << "'s Private Key" << RESET << endl;

    for (long long exp = p - 1; exp >= 1; --exp) {
        long long res = modexp(g, exp, p);
        cout << ORANGE << "[#]" << RESET << " Trying g^" << GREEN << exp << RESET << " mod " << RED << p << RESET << " = " << RED << res << RESET;
        if (res == publicKey) {
            cout << "  <-- Match found! Private key of " << RED << victim << RESET << " = " << GREEN << exp << RESET << endl;
            return exp;
        }
        cout << endl;
    }
    cout << RED << "[x]" << RESET << " No match found for " << RED << victim << RESET << endl;
    return -1;
}

void DiffieHellmanMITM::simulate(long long g, long long p, long long A_public, long long B_public) {
    long long Xa = bruteForce(g, p, A_public, "A");
    long long Xb = bruteForce(g, p, B_public, "B");

    if (Xa == -1 || Xb == -1) {
        cout << RED << "[!]" << RESET << " Could not recover private keys, aborting attack.\n";
        return;
    }

    long long K1 = modexp(B_public, Xa, p); // what A computes
    long long K2 = modexp(A_public, Xb, p); // what B computes

    cout << endl;
    cout << GREEN << "   Shared Secret Computation using recovered private keys" << RESET << endl;
    cout << ORANGE << "[#]" << RESET << " Using " << RED << "B" << RESET << "_public^X" << GREEN << "a" << RESET << " mod " << RED << "p" << RESET << " = " << RED << B_public << RESET << "^" << GREEN << Xa << RESET << " mod " << RED << p << RESET << " = " << GREEN << K1 << RESET << endl;
    cout << ORANGE << "[#]" << RESET << " Using " << RED << "A" << RESET << "_public^X" << GREEN << "b" << RESET << " mod " << RED << "p" << RESET << " = " << RED << A_public << RESET << "^" << GREEN << Xb << RESET << " mod " << RED << p << RESET << " = " << GREEN << K2 << RESET << endl;

    if (K1 == K2) {
        cout << BLUE << "_________________________________________________________________\n" << RESET;
        cout << endl;
        cout << GREEN << "[-]" << RESET << " Success! Shared secret between A and B is " << GREEN << K1 << RESET << endl;
        cout << BLUE << "_________________________________________________________________\n" << RESET;
    } else {
        cout << BLUE << "_________________________________________________________________\n" << RESET;
        cout << endl;
        cout << RED << "[x]" << RESET << " Mismatch: Something went wrong, keys do not match.\n";
        cout << BLUE << "_________________________________________________________________\n" << RESET;
    }

    cout << endl;
    cout << ORANGE << "[!]" << RESET << " >>> Attacker can now decrypt all communications.\n";
}
