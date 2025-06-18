#include "hexadecimal.h"
#include <sstream>
#include <iomanip>
#include <iostream>

using namespace std;

vector<string> Hexadecimal::calculateChecksum(const vector<vector<string>>& blocks) {
    if (blocks.empty()) return {};

    size_t width = blocks[0].size();
    vector<int> sums(width, 0);

    for (const auto& block : blocks) {
        for (size_t i = 0; i < block.size(); ++i) {
            int value;
            stringstream ss;
            ss << hex << block[i];
            ss >> value;
            sums[i] += value;
        }
    }

    vector<string> checksum;
    for (int sum : sums) {
        stringstream ss;
        ss << uppercase << setfill('0') << setw(2) << hex << (sum % 256);  // Wrap at 256
        checksum.push_back(ss.str());
    }

    return checksum;
}
