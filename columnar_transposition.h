#ifndef COLUMNAR_TRANSPOSITION_H
#define COLUMNAR_TRANSPOSITION_H

#include <string>
#include <vector>

class ColumnarTransposition {
public:
    ColumnarTransposition(const std::string& key);
    
    std::string encrypt(const std::string& plaintext);
    std::string decrypt(const std::string& ciphertext);

private:
    std::string key;
    std::vector<int> keyOrder;

    void generateKeyOrder();
    std::string removeSpaces(const std::string& input);
    std::string addPadding(const std::string& input);
    std::string removePadding(const std::string& input);
};

#endif
