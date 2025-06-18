#ifndef MINIRSA_H
#define MINIRSA_H

#include <string>

class MiniRSA {
public:
    MiniRSA(const std::string& N_str, const std::string& e_str, const std::string& c_str);
    std::string decrypt();

private:
    std::string N_str, e_str, c_str;
};

#endif // MINIRSA_H
