#include "HashIdentifier.h"
#include <regex>
#include <string>

std::string identifyHashLocally(const std::string& hash) {
    size_t len = hash.length();

    if (std::regex_match(hash, std::regex("^[a-fA-F0-9]+$"))) {
        switch (len) {
            case 13: return "MySQL (Old format)";
            case 16: return "LM hash (Windows LAN Manager)";
            case 32: return "MD5 (128-bit) or NTLM";
            case 40: return "SHA-1 (160-bit) or MySQL5";
            case 64: return "SHA-256 (256-bit) or RIPEMD-160";
            case 96: return "SHA-384 (384-bit)";
            case 128: return "SHA-512 (512-bit) or Whirlpool";
            default: return "Unknown hash (hex format)";
        }
    } else if (std::regex_match(hash, std::regex("^[a-zA-Z0-9+/=]+$"))) {
        return "Possible Base64-encoded hash";
    } else {
        return "Unknown format or unsupported hash type";
    }
}
