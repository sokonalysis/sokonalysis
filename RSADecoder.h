#ifndef RSADecoder_H
#define RSADecoder_H

#include <string>

class RSADecoder {
public:
    static std::string fixPemFormat(const std::string& input);
    static void decodeCertificate(const std::string& pemCert);
};

#endif // RSADecoder_H
