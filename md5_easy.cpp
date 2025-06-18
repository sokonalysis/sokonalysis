#define CRYPTOPP_ENABLE_NAMESPACE_WEAK 1

#include "md5_easy.h"
#include <cryptopp/md5.h>
#include <cryptopp/filters.h>
#include <cryptopp/hex.h>

using namespace CryptoPP;

std::string generateMD5(const std::string& input) {
    std::string digest;

    Weak::MD5 hash;
    StringSource(input, true,
        new HashFilter(hash,
            new HexEncoder(
                new StringSink(digest), false // lowercase
            )
        )
    );

    return digest;
}