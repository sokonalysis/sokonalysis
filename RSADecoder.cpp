#include "RSADecoder.h"
#include <iostream>
#include <algorithm>
#include <cctype>

#include <openssl/bio.h>
#include <openssl/x509.h>
#include <openssl/evp.h>
#include <openssl/pem.h>
#include <openssl/core_names.h>   // <== Must include for OSSL_PKEY_PARAM_RSA_N etc.
#include <openssl/bn.h>

// Set colors
#define GREEN   "\033[32m"
#define CYAN    "\033[36m"
#define BLUE    "\033[34m"
#define MAGENTA "\033[35m"
#define YELLOW  "\033[33m"
#define WHITE   "\033[37m"
#define RED     "\033[31m"
#define ORANGE "\033[38;5;208m"
#define BOLD    "\033[1m"
#define CLEAR   "\033[2J\033[H"  // Clears screen and moves cursor to top-left
#define RESET   "\033[0m"

static void printBN(const char* msg, const BIGNUM* bn) {
    if (!bn) return;
    char* bn_hex = BN_bn2hex(bn);
    if (bn_hex) {
        std::cout << msg << ": " << bn_hex << std::endl;
        OPENSSL_free(bn_hex);
    }
}

std::string RSADecoder::fixPemFormat(const std::string& input) {
    std::string pem = input;
    const std::string header = "-----BEGIN CERTIFICATE-----";
    const std::string footer = "-----END CERTIFICATE-----";

    size_t header_pos = pem.find(header);
    size_t footer_pos = pem.find(footer);
    if (header_pos == std::string::npos || footer_pos == std::string::npos)
        return {};

    size_t base64_start = header_pos + header.length();
    std::string base64_data = pem.substr(base64_start, footer_pos - base64_start);

    // Remove whitespace from base64_data
    base64_data.erase(std::remove_if(base64_data.begin(), base64_data.end(),
        [](unsigned char c) { return std::isspace(c); }), base64_data.end());

    std::string fixed_pem = header + "\n";
    for (size_t i = 0; i < base64_data.size(); i += 64) {
        fixed_pem += base64_data.substr(i, 64) + "\n";
    }
    fixed_pem += footer + "\n";

    return fixed_pem;
}

void RSADecoder::decodeCertificate(const std::string& pemCert) {
    std::string fixedPem = fixPemFormat(pemCert);
    if (fixedPem.empty()) {
        std::cout << BLUE << "_________________________________________________________________\n" << RESET;
        std::cout << std::endl;
        std::cerr << RED << "[!]" << RESET << " Invalid PEM certificate format\n";
        std::cout << BLUE << "_________________________________________________________________\n" << RESET;
        return;
    }

    BIO* bio = BIO_new_mem_buf(fixedPem.data(), (int)fixedPem.size());
    if (!bio) {
        std::cout << BLUE << "_________________________________________________________________\n" << RESET;
        std::cout << std::endl;
        std::cerr << RED << "[x]" << RESET << " Failed to create BIO\n";
        std::cout << BLUE << "_________________________________________________________________\n" << RESET;
        return;
    }

    X509* cert = PEM_read_bio_X509(bio, nullptr, nullptr, nullptr);
    if (!cert) {
        std::cout << BLUE << "_________________________________________________________________\n" << RESET;
        std::cout << std::endl;
        std::cerr << RED << "[x]" << RESET << " Failed to parse certificate\n";
        std::cout << BLUE << "_________________________________________________________________\n" << RESET;
        BIO_free(bio);
        return;
    }

    // Print Subject
    X509_NAME* subjectName = X509_get_subject_name(cert);
    if (subjectName) {
        char buf[256];
        X509_NAME_oneline(subjectName, buf, sizeof(buf));
        std::cout << BLUE << "_________________________________________________________________\n" << RESET;
        std::cout << std::endl;
        std::cout << GREEN << "[-]" << RESET << " Subject: " << GREEN << buf << RESET <<  std::endl;
    }

    // Print Issuer
    X509_NAME* issuerName = X509_get_issuer_name(cert);
    if (issuerName) {
        char buf[256];
        X509_NAME_oneline(issuerName, buf, sizeof(buf));
        std::cout << GREEN << "[-]" << RESET << " Issuer: " << GREEN << buf << RESET << std::endl;
    }

    EVP_PKEY* pubkey = X509_get_pubkey(cert);
    if (!pubkey) {
        std::cout << BLUE << "_________________________________________________________________\n" << RESET;
        std::cout << std::endl;
        std::cerr << RED << "[!]" << RESET << " No public key found in certificate\n";
        std::cout << BLUE << "_________________________________________________________________\n" << RESET;
        X509_free(cert);
        BIO_free(bio);
        return;
    }

    int key_type = EVP_PKEY_id(pubkey);
    std::cout << GREEN << "[-]" << RESET << " Public Key Algorithm: " << GREEN << OBJ_nid2ln(key_type) << RESET << std::endl;

    if (key_type == EVP_PKEY_RSA) {
        BIGNUM* n = nullptr;
        BIGNUM* e = nullptr;

        if (EVP_PKEY_get_bn_param(pubkey, OSSL_PKEY_PARAM_RSA_N, &n) &&
                EVP_PKEY_get_bn_param(pubkey, OSSL_PKEY_PARAM_RSA_E, &e)) {
                std::cout << GREEN << "[-]" << RESET << " Public Key Algorithm: " << GREEN << "rsaEncryption\n";

                int bits = BN_num_bits(n);
                std::cout << GREEN << "[-]" << RESET << " RSA Public-Key: (" << GREEN << bits << RESET << " bit)\n";

                std::cout << GREEN << "[-]" << RESET << " Modulus: " << GREEN << BN_bn2dec(n) << RESET << " (0x" << GREEN << BN_bn2hex(n) << RESET << ")\n";
                std::cout << GREEN << "[-]" << RESET << " Exponent: " << GREEN << BN_bn2dec(e) << RESET << " (0x" << GREEN << BN_bn2hex(e) << RESET << ")\n";
                std::cout << BLUE << "_________________________________________________________________\n" << RESET;
        
                BN_free(n);
                BN_free(e);
                } else {
                            std::cerr << RED << "[x]" << RESET << " Failed to get RSA parameters using OpenSSL 3 API\n";
                }
                } else {
                            std::cerr << RED << "[x]" << RESET << " Public key is not RSA\n";
                }

    EVP_PKEY_free(pubkey);
    X509_free(cert);
    BIO_free(bio);
}
