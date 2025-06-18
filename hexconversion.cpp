#include "hexconversion.h"
#include <sstream>
#include <iomanip>
#include <iostream>

std::string HexConversion::textToHex(const std::string& text) {
    std::stringstream ss;
    for (char c : text) {
        ss << std::hex << std::uppercase << std::setw(2) << std::setfill('0') << (int)c << " ";
    }
    return ss.str();
}

std::string HexConversion::hexToText(const std::string& hexStr) {
    std::stringstream input(hexStr), output;
    std::string hexVal;
    while (input >> hexVal) {
        int ch;
        std::stringstream converter;
        converter << std::hex << hexVal;
        converter >> ch;
        output << static_cast<char>(ch);
    }
    return output.str();
}
