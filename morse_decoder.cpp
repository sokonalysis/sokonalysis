#include "morse_decoder.h"
#include <unordered_map>
#include <sstream>
#include <cctype>

static const std::unordered_map<std::string, char> morseMap = {
    {".-", 'A'},   {"-...", 'B'}, {"-.-.", 'C'}, {"-..", 'D'},
    {".", 'E'},    {"..-.", 'F'}, {"--.", 'G'},  {"....", 'H'},
    {"..", 'I'},   {".---", 'J'}, {"-.-", 'K'},  {".-..", 'L'},
    {"--", 'M'},   {"-.", 'N'},   {"---", 'O'},  {".--.", 'P'},
    {"--.-", 'Q'}, {".-.", 'R'},  {"...", 'S'},  {"-", 'T'},
    {"..-", 'U'},  {"...-", 'V'}, {".--", 'W'},  {"-..-", 'X'},
    {"-.--", 'Y'}, {"--..", 'Z'}, {"-----", '0'}, {".----", '1'},
    {"..---", '2'}, {"...--", '3'}, {"....-", '4'}, {".....", '5'},
    {"-....", '6'}, {"--...", '7'}, {"---..", '8'}, {"----.", '9'},
    {".-.-.-", '.'}, {"--..--", ','}, {"..--..", '?'}, {"-.-.--", '!'},
    {"-....-", '-'}, {"-..-.", '/'}, {".--.-.", '@'}, {"-.--.", '('},
    {"-.--.-", ')'}, {".-...", '&'}, {"---...", ':'}, {"-.-.-.", ';'},
    {"-...-", '='}, {".-.-.", '+'}, {"..--.-", '_'}, {".-..-.", '"'}
};

std::string MorseDecoder::decode(const std::string& morseCode) {
    std::istringstream stream(morseCode);
    std::string token;
    std::string result;

    while (stream >> token) {
        if (token == "/") {
            result += ' ';
        } else if (morseMap.find(token) != morseMap.end()) {
            result += morseMap.at(token);
        } else {
            // If not a valid Morse token, assume it's a raw character or symbol
            result += token;
        }
    }

    return result;
}
