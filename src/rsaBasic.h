#ifndef RSA_H
#define RSA_H

#include <vector>
#include <string>

bool is_prime(int num);
int gcd(int a, int b);
int mod_inverse(int e, int m);
int letter_to_number(char letter, int mapping);
char number_to_letter(int num, int mapping);
int mod_exp(int base, int exp, int mod);
std::vector<int> encrypt_message(const std::string& message, int e, int n, int mapping);
std::string decrypt_message(const std::vector<int>& encrypted_message, int d, int n, int mapping);

#endif // RSA_H