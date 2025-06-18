#include "modulus.h"
#include <stdexcept>

int modulus_operation(int a, int b) {
    if (b == 0) {
        throw std::invalid_argument("Division by zero is undefined.");
    }
    return a % b;
}
