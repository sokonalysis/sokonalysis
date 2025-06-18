#ifndef MORSE_DECODER_H
#define MORSE_DECODER_H

#include <string>

class MorseDecoder {
public:
    static std::string decode(const std::string& morseCode);
};

#endif // MORSE_DECODER_H
