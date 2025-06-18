#include "rsaCTFen.h"

#include <cryptlib.h>
#include <integer.h>
#include <nbtheory.h>
#include <secblock.h>
#include <iostream>
#include <sstream>

using namespace CryptoPP;

std::string decryptRSAWithNandE(const std::string& c_str, const std::string& e_str, const std::string& n_str) {
    try {
        Integer n(n_str.c_str());
        Integer e(e_str.c_str());
        Integer c(c_str.c_str());

        Integer p, q;
        bool found = false;

        // Trial division factoring (slow for large n)
        for (word64 i = 2; i < 10000000; ++i) {
            if (n % Integer(i) == 0) {
                p = Integer(i);
                q = n / p;
                found = true;
                break;
            }
        }

        if (!found) {
            return "[!] Could not factor modulus n (try FactorDB for large n)";
        }

        Integer phi = (p - Integer::One()) * (q - Integer::One());
        Integer d = e.InverseMod(phi);
        Integer m = a_exp_b_mod_c(c, d, n);

        // Convert to byte array then string
        SecByteBlock bytes(m.MinEncodedSize());
        m.Encode(bytes, bytes.size());

        return std::string(reinterpret_cast<const char*>(bytes.begin()), bytes.size());
    }
    catch (const CryptoPP::Exception& ex) {
        return std::string("[!] Crypto++ Error: ") + ex.what();
    }
    catch (const std::exception& ex) {
        return std::string("[!] Error: ") + ex.what();
    }
}
