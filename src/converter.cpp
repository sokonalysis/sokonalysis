#include "converter.h"
#include <cctype>
#include <iostream>

int Converter::letterToNumber(char letter, int mapping) {
    if (std::isalpha(letter)) {
        int base = (mapping == 1) ? 1 : 0;  // A=1 or A=0 mapping
        return std::toupper(letter) - 'A' + base;
    }
    throw std::invalid_argument("Invalid character for letterToNumber");
}

char Converter::numberToLetter(int number, int mapping) {
    int base = (mapping == 1) ? 1 : 0;  // A=1 or A=0 mapping
    
    // Handle wraparound by using modulo
    number = (number - base) % 26 + base;
    
    if (number < base || number > (25 + base)) {
        throw std::out_of_range("Number out of valid range.");
    }

    return static_cast<char>('A' + number - base);
}

std::vector<int> Converter::stringToNumbers(const std::string& input, int mapping) {
    std::vector<int> result;
    for (char c : input) {
        if (std::isalpha(c)) {
            result.push_back(letterToNumber(c, mapping));
        }
    }
    return result;
}

std::string Converter::numbersToString(const std::vector<int>& numbers, int mapping) {
    std::string result;
    for (int n : numbers) {
        result += numberToLetter(n, mapping);  // This will handle wraparound
    }
    return result;
}
