#ifndef CONVERTER_H
#define CONVERTER_H

#include <string>
#include <vector>

class Converter {
public:
    // Converts a letter to a number (based on mapping: 1 for A=1, 2 for A=0)
    static int letterToNumber(char letter, int mapping);

    // Converts a number to a letter (based on mapping)
    static char numberToLetter(int number, int mapping);

    // Converts string to vector of numbers
    static std::vector<int> stringToNumbers(const std::string& input, int mapping);

    // Converts vector of numbers to string
    static std::string numbersToString(const std::vector<int>& numbers, int mapping);
};

#endif
