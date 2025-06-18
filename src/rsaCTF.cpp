// rsaCTF.cpp
#include "rsaCTF.h"
#include <iostream>
#include <cryptlib.h>
#include <integer.h>
#include <nbtheory.h>
#include <secblock.h>
#include <sstream>
#include <iomanip>

using namespace CryptoPP;

std::string decryptRSA(const std::string& c_str, const std::string& e_str, const std::string& p_str, const std::string& q_str) {
    try {
        Integer p(p_str.c_str());
        Integer q(q_str.c_str());
        Integer e(e_str.c_str());
        Integer c(c_str.c_str());

        Integer n = p * q;
        Integer phi = (p - Integer::One()) * (q - Integer::One());
        Integer d = e.InverseMod(phi);

        Integer m = a_exp_b_mod_c(c, d, n);

        // Convert decrypted Integer (m) to byte array
        SecByteBlock bytes(m.MinEncodedSize());
        m.Encode(bytes, bytes.size());

        // Convert byte array to ASCII string
        std::string plaintext(reinterpret_cast<const char*>(bytes.begin()), bytes.size());
        return plaintext;

    } catch (const Exception& ex) {
        return std::string("[!] Crypto++ Error: ") + ex.what();
    } catch (const std::exception& ex) {
        return std::string("[!] Error: ") + ex.what();
    }
}
