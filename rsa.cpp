#include "rsa.h"
#include <cmath>

// Function to check if a number is prime
bool is_prime(int num) {
    if (num <= 1) return false;
    for (int i = 2; i <= sqrt(num); i++) {
        if (num % i == 0) return false;
    }
    return true;
}

// Function to find the greatest common divisor (GCD)
int gcd(int a, int b) {
    while (b != 0) {
        int temp = b;
        b = a % b;
        a = temp;
    }
    return a;
}

// Function to find the modular inverse using the Extended Euclidean Algorithm
int mod_inverse(int e, int m) {
    int m0 = m, t, q;
    int x0 = 0, x1 = 1;

    if (m == 1) return 0;

    while (e > 1) {
        q = e / m;
        t = m;
        m = e % m;
        e = t;
        t = x0;
        x0 = x1 - q * x0;
        x1 = t;
    }

    if (x1 < 0) x1 += m0;

    return x1;
}

// Function to convert a letter to its corresponding number based on mapping style
int letter_to_number(char letter, int mapping) {
    return (mapping == 1) ? (letter - 'A' + 1) : (letter - 'A');
}

// Function to convert a number back to its corresponding letter based on mapping style
char number_to_letter(int num, int mapping) {
    return (mapping == 1) ? char(num + 'A' - 1) : char(num + 'A');
}

// Function to perform modular exponentiation (base^exp % mod)
int mod_exp(int base, int exp, int mod) {
    int result = 1;
    base = base % mod;

    while (exp > 0) {
        if (exp % 2 == 1) {
            result = (result * base) % mod;
        }
        exp = exp >> 1;
        base = (base * base) % mod;
    }

    return result;
}

// Function to encrypt the message using RSA
std::vector<int> encrypt_message(const std::string& message, int e, int n, int mapping) {
    std::vector<int> encrypted_message;
    for (char letter : message) {
        int num = letter_to_number(letter, mapping);  // Pass mapping to letter_to_number
        int encrypted_num = mod_exp(num, e, n);  // Encryption using RSA
        encrypted_message.push_back(encrypted_num);
    }
    return encrypted_message;
}

// Function to decrypt the message using RSA
std::string decrypt_message(const std::vector<int>& encrypted_message, int d, int n, int mapping) {
    std::string decrypted_message;
    for (int cipher : encrypted_message) {
        int m = mod_exp(cipher, d, n);  // Decryption using RSA
        decrypted_message += number_to_letter(m, mapping);  // Pass mapping to number_to_letter
    }
    return decrypted_message;
}
