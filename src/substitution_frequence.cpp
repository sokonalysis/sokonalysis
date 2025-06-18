#include "substitution_frequence.h"
#include <string>
#include <array>
#include <cstdio>
#include <algorithm>  // for isspace()

std::string SubstitutionPythonSolver::decryptWithPython(const std::string& ciphertext) const {
    // Escape double quotes in ciphertext
    std::string safeCiphertext = ciphertext;
    size_t pos = 0;
    while ((pos = safeCiphertext.find('"', pos)) != std::string::npos) {
        safeCiphertext.replace(pos, 1, "\\\"");
        pos += 2; // move past escaped quote
    }

    // Build command to run the Python script with ciphertext argument
    std::string command = "python solve_sub.py \"" + safeCiphertext + "\"";

    std::array<char, 256> buffer;
    std::string result;

    FILE* pipe = _popen(command.c_str(), "r"); // Windows
    if (!pipe) {
        return "[!] Failed to run Python script.";
    }

    // Read script output
    while (fgets(buffer.data(), buffer.size(), pipe) != nullptr) {
        result += buffer.data();
    }
    _pclose(pipe);

    // Trim trailing whitespace/newlines
    while (!result.empty() && (result.back() == '\n' || result.back() == '\r' || isspace(result.back()))) {
        result.pop_back();
    }

    return result;
}
