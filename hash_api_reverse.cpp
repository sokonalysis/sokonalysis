#include "hash_api_reverse.h"
#include <curl/curl.h>
#include <sstream>

static size_t WriteCallback(void* contents, size_t size, size_t nmemb, std::string* output) {
    output->append((char*)contents, size * nmemb);
    return size * nmemb;
}

std::string reverseHashViaAPI(const std::string& hash, const std::string& hashType) {
    CURL* curl;
    CURLcode res;
    std::string readBuffer;

    std::string url = "https://md5decrypt.net/en/Api/api.php?hash=" + hash +
        "&hash_type=" + hashType +
        "&email=s0k0j4m3s@gmail.com&code=688501c75f1a0dfc";

    curl = curl_easy_init();
    if (curl) {
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);

        // 🔧 Add User-Agent to avoid 403 errors
        curl_easy_setopt(curl, CURLOPT_USERAGENT, "Mozilla/5.0 (Windows NT 10.0; Win64; x64)");

        res = curl_easy_perform(curl);

        if (res != CURLE_OK) {
            readBuffer = "cURL error: " + std::string(curl_easy_strerror(res));
        }

        curl_easy_cleanup(curl);
    }

    return readBuffer.empty() ? "No result from API." : readBuffer;
}
