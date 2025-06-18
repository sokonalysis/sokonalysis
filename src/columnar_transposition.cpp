#include "columnar_transposition.h"
#include <iostream>
#include <algorithm>
#include <cmath>
#include <sstream>

ColumnarTransposition::ColumnarTransposition(const std::string& key) : key(key) {
    generateKeyOrder();
}

void ColumnarTransposition::generateKeyOrder() {
    std::string tempKey = key;
    int len = tempKey.length();
    
    std::vector<std::pair<char, int>> orderedKey;
    for (int i = 0; i < len; ++i) {
        orderedKey.push_back({tempKey[i], i});
    }

    std::sort(orderedKey.begin(), orderedKey.end());

    for (const auto& pair : orderedKey) {
        keyOrder.push_back(pair.second);
    }
}

std::string ColumnarTransposition::removeSpaces(const std::string& input) {
    std::string result = input;
    result.erase(std::remove(result.begin(), result.end(), ' '), result.end());
    return result;
}

std::string ColumnarTransposition::addPadding(const std::string& input) {
    int len = input.length();
    int keyLength = key.length();
    int paddingNeeded = keyLength - (len % keyLength);

    if (paddingNeeded == keyLength) {
        return input;  // No padding needed
    }

    return input + std::string(paddingNeeded, 'X');  // Add padding 'X'
}

std::string ColumnarTransposition::removePadding(const std::string& input) {
    size_t pos = input.find_last_not_of('X');
    if (pos != std::string::npos) {
        return input.substr(0, pos + 1);  // Remove padding
    }
    return input;  // No padding
}

std::string ColumnarTransposition::encrypt(const std::string& plaintext) {
    std::string cleanText = addPadding(removeSpaces(plaintext));  // Add padding
    int textLength = cleanText.length();
    int numColumns = key.length();
    int numRows = std::ceil(static_cast<double>(textLength) / numColumns);
    
    std::vector<std::vector<char>> grid(numRows, std::vector<char>(numColumns, ' '));

    // Fill grid with characters from the plaintext
    int index = 0;
    for (int row = 0; row < numRows; ++row) {
        for (int col = 0; col < numColumns; ++col) {
            if (index < textLength) {
                grid[row][col] = cleanText[index++];
            }
        }
    }

    // Read columns in the order of the key order
    std::string ciphertext;
    for (int col : keyOrder) {
        for (int row = 0; row < numRows; ++row) {
            if (grid[row][col] != ' ') {
                ciphertext += grid[row][col];
            }
        }
    }

    return ciphertext;
}

std::string ColumnarTransposition::decrypt(const std::string& ciphertext) {
    int numColumns = key.length();
    int numRows = std::ceil(static_cast<double>(ciphertext.length()) / numColumns);
    
    std::vector<std::vector<char>> grid(numRows, std::vector<char>(numColumns, ' '));

    // Fill grid column by column using key order
    int index = 0;
    for (int col : keyOrder) {
        for (int row = 0; row < numRows; ++row) {
            if (index < ciphertext.length()) {
                grid[row][col] = ciphertext[index++];
            }
        }
    }

    // Read the grid row by row
    std::string plaintext;
    for (int row = 0; row < numRows; ++row) {
        for (int col = 0; col < numColumns; ++col) {
            if (grid[row][col] != ' ') {
                plaintext += grid[row][col];
            }
        }
    }

    return removePadding(plaintext);  // Remove padding after decryption
}
