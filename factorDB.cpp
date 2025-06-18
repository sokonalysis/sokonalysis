// factorDB.cpp
#include "factorDB.h"
#include <iostream>
#include <curl/curl.h>
#include <nlohmann/json.hpp>


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

using json = nlohmann::json;
using namespace std;

static size_t WriteCallback(void* contents, size_t size, size_t nmemb, string* output) {
    size_t totalSize = size * nmemb;
    output->append((char*)contents, totalSize);
    return totalSize;
}

void queryFactorDB(const std::string& modulus) {
    CURL* curl = curl_easy_init();
    string readBuffer;

    if (curl) {
        string url = "http://factordb.com/api?query=" + modulus;

        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);

        CURLcode res = curl_easy_perform(curl);
        curl_easy_cleanup(curl);

        if (res == CURLE_OK) {
            try {
                json response = json::parse(readBuffer);

                cout << ORANGE << "\n[*]" << RESET << " Status: " << ORANGE << response["status"] << RESET << endl;
                auto factors = response["factors"];
                cout << GREEN <<  "[-]" << RESET << " Factors:\n";
                cout << BLUE << "_________________________________________________________________\n" << RESET;
                cout << endl;
                if (factors.size() == 1 && factors[0][1] == "2") {
                        cout << GREEN << "[-] " << RESET << "n = p^2, where p = " << GREEN << factors[0][0] 
                        << RESET << " (exponent " << GREEN << "2" << RESET << ")\n";
                } else {
                            for (size_t i = 0; i < factors.size(); ++i) {
                                    string label;
                                    if (i == 0) label = "p";
                                        else if (i == 1) label = "q";
                                                else label = "r" + to_string(i - 1);  // Optional extra primes

        cout << GREEN << "[-] " << RESET << label << " = " << GREEN << factors[i][0] 
             << RESET << " (exponent " << GREEN << factors[i][1] << RESET << ")\n";
    }
}

                cout << BLUE << "_________________________________________________________________\n" << RESET;
            } catch (...) {
                cerr << RED<< "[!]" << RESET << " Failed to parse FactorDB response.\n";
            }
        } else {
            cerr << RED << "[!]" << RESET << " CURL request failed: " << curl_easy_strerror(res) << endl;
        }
    } else {
        cerr << RED << "[!]" << RESET << " CURL initialization failed.\n";
    }
}
