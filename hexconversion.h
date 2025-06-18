#ifndef HEXCONVERSION_H
#define HEXCONVERSION_H

#include <string>

class HexConversion {
public:
    static std::string textToHex(const std::string& text);
    static std::string hexToText(const std::string& hexStr);
};

#endif
