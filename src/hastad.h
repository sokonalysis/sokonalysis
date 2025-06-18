#ifndef HASTAD_H
#define HASTAD_H

#include <vector>
#include <string>
#include <gmpxx.h>

mpz_class chinese_remainder(const std::vector<mpz_class>& c, const std::vector<mpz_class>& n);
mpz_class integer_nth_root(mpz_class x, unsigned int n);
std::string decrypt_message(const std::vector<mpz_class>& c, const std::vector<mpz_class>& n, unsigned int e);

#endif // HASTAD_H
