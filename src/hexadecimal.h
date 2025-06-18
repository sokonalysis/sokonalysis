#ifndef HEXADECIMAL_H
#define HEXADECIMAL_H

#include <vector>
#include <string>

class Hexadecimal {
public:
    static std::vector<std::string> calculateChecksum(const std::vector<std::vector<std::string>>& blocks);
};

#endif