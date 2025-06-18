#ifndef SUBSTITUTION_PYTHON_H
#define SUBSTITUTION_PYTHON_H

#include <string>

// Class to decrypt substitution cipher text using a Python script
class SubstitutionPythonSolver {
public:
    // Calls the Python script to decrypt the given ciphertext
    std::string decryptWithPython(const std::string& ciphertext) const;
};

#endif // SUBSTITUTION_PYTHON_H
