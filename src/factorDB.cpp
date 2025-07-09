// factorDB.cpp
#include "factorDB.h"
#include <iostream>
#include <curl/curl.h>
#include <nlohmann/json.hpp>
#include <cctype>
#include <algorithm>

#define GREEN   "\033[32m"
#define CYAN    "\033[36m"
#define BLUE    "\033[34m"
#define MAGENTA "\033[35m"
#define YELLOW  "\033[33m"
#define WHITE   "\033[37m"
#define RED     "\033[31m"
#define ORANGE  "\033[38;5;208m"
#define BOLD    "\033[1m"
#define CLEAR   "\033[2J\033[H"
#define RESET   "\033[0m"

using json = nlohmann::json;
using namespace std;

static size_t WriteCallback(void* contents, size_t size, size_t nmemb, string* output) {
    size_t totalSize = size * nmemb;
    output->append((char*)contents, totalSize);
    return totalSize;
}

// Helper: resolve factor ID via FactorDB API
string resolveFactor(const string& factorID) {
    if (all_of(factorID.begin(), factorID.end(), ::isdigit)) {
        return factorID; // already a number
    }

    CURL* curl = curl_easy_init();
    string buffer;

    if (curl) {
        string url = "http://factordb.com/api?query=" + factorID;
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &buffer);
        CURLcode res = curl_easy_perform(curl);
        curl_easy_cleanup(curl);

        if (res == CURLE_OK) {
            try {
                json j = json::parse(buffer);
                if (j.contains("number")) {
                    return j["number"].get<string>();
                }
            } catch (...) {
                return "[parse error]";
            }
        }
    }

    return "[unresolved]";
}

void queryFactorDB(const string& modulus) {
    CURL* curl = curl_easy_init();
    string readBuffer;

    if (!curl) {
        cerr << RED << "[!]" << RESET << " CURL initialization failed.\n";
        return;
    }

    string url = "http://factordb.com/api?query=" + modulus;
    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);

    CURLcode res = curl_easy_perform(curl);
    curl_easy_cleanup(curl);

    if (res != CURLE_OK) {
        cerr << RED << "[!]" << RESET << " CURL request failed: " << curl_easy_strerror(res) << endl;
        return;
    }

    try {
        json response = json::parse(readBuffer);

        cout << ORANGE << "\n[*]" << RESET << " Status: " << ORANGE << response["status"] << RESET << endl;
        auto factors = response["factors"];

        if (!factors.is_array()) {
            cerr << RED << "[!]" << RESET << " Unexpected response format.\n";
            return;
        }

        cout << GREEN << "[-]" << RESET << " Factors:\n";
        cout << BLUE << "_________________________________________________________________\n" << RESET;

        for (size_t i = 0; i < factors.size(); ++i) {
            string label;
            if (i == 0) label = "p";
            else if (i == 1) label = "q";
            else label = "r" + to_string(i - 1);

            string id = factors[i][0].get<string>();
            int exponent = factors[i][1].get<int>();
            string resolvedValue = resolveFactor(id);

            cout << GREEN << "[-] " << RESET << label << " = " << GREEN << resolvedValue
                 << RESET << " (exponent " << GREEN << exponent << RESET << ")\n";
        }

        cout << BLUE << "_________________________________________________________________\n" << RESET;
    } catch (...) {
        cerr << RED << "[!]" << RESET << " Failed to parse FactorDB response or resolve factors.\n";
    }
}
