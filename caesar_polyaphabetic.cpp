// caesar_polyalphabetic.cpp
#include "caesar_polyalphabetic.h"
#include <cctype>

using namespace std;

string caesar_polyalphabetic_encrypt(const string& message, const string& keyword, int mapping) {
    string encrypted_message = "";
    int key_length = keyword.length();
    
    for (int i = 0; i < message.length(); ++i) {
        char m = message[i];
        if (isalpha(m)) {
            int shift = (toupper(keyword[i % key_length]) - 'A');
            if (mapping == 2) {
                shift = (toupper(keyword[i % key_length]) - 'A' + 1) % 26;
            }
            
            if (isupper(m)) {
                encrypted_message += char((m - 'A' + shift) % 26 + 'A');
            } else if (islower(m)) {
                encrypted_message += char((m - 'a' + shift) % 26 + 'a');
            }
        } else {
            encrypted_message += m; // Non-alphabet characters remain unchanged
        }
    }
    
    return encrypted_message;
}

string caesar_polyalphabetic_decrypt(const string& message, const string& keyword, int mapping) {
    string decrypted_message = "";
    int key_length = keyword.length();
    
    for (int i = 0; i < message.length(); ++i) {
        char m = message[i];
        if (isalpha(m)) {
            int shift = (toupper(keyword[i % key_length]) - 'A');
            if (mapping == 2) {
                shift = (toupper(keyword[i % key_length]) - 'A' + 1) % 26;
            }
            
            if (isupper(m)) {
                decrypted_message += char((m - 'A' - shift + 26) % 26 + 'A');
            } else if (islower(m)) {
                decrypted_message += char((m - 'a' - shift + 26) % 26 + 'a');
            }
        } else {
            decrypted_message += m; // Non-alphabet characters remain unchanged
        }
    }
    
    return decrypted_message;
}
