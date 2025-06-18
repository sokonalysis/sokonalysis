#ifndef SUBSTITUTION_H
#define SUBSTITUTION_H

#include <string>
#include <map>
#include <vector>

class SubstitutionCipher {
private:
    std::string key;
    std::map<char, char> encMap;
    std::map<char, char> decMap;

    void buildMaps();

public:
    SubstitutionCipher();
    void setKey(const std::string& k);
    std::string encrypt(const std::string& plaintext);
    std::string decrypt(const std::string& ciphertext);
};

#endif
