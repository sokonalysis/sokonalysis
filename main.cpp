#include <iostream>
#include "rsa.h"
#include "caesar.h"
#include "transposition.h"
#include "railfence.h"
#include "b_caesar.h"

using namespace std;

int main() {
    cout << "\033[32m" << endl;
    // Display the logo at the start of the program
    cout << endl;
    cout << " SSSSS   OOOOO  K   K  OOOOO  N   N   AAAAA  L     Y   Y  SSSSS   I   SSSSS " << endl;
    cout << "S        O   O  K  K   O   O  NN  N  A     A L      Y Y  S        I  S      " << endl;
    cout << "  SSS    O   O  KKK    O   O  N N N  AAAAAAA L       Y     SSS    I    SSS  " << endl;
    cout << "      S  O   O  K  K   O   O  N  NN  A     A L       Y         S  I        S" << endl;
    cout << " SSSSS   OOOOO  K   K  OOOOO  N   N  A     A LLLLL   Y    SSSSS   I  SSSSS  " << endl;
    cout << endl;
    cout << "\033[32m" << endl;

    string choice;
    bool running = true;

    cout << endl;

    cout << "\033[32m" << endl;

    while (running) {
        cout << "Sokonalysis - Crypto Tool | Created by James Soko" << endl;
        cout << "--------------------------------------------------" << endl;
        cout << "[1] RSA" << endl;
        cout << "[2] Caesar" << endl;
        cout << "[3] Transposition" << endl;
        cout << "[4] Railfence" << endl;
        cout << "[5] Caesar Brute Force" << endl;
        cout << "--------------------------------------------------" << endl;
        cout << endl;
        cout << "Select an Algorithm: ";
        cin >> choice;

        cout << endl;

        // Ask the user for the shift mapping style
        int mapping;
        cout << "Select the letter-to-number mapping style:" << endl;
        cout << "------------------------------------------------" << endl;
        cout << "1. A=1, B=2, ..., Z=26" << endl;
        cout << "2. A=0, B=1, ..., Z=25" << endl;
        cout << "------------------------------------------------" << endl;
        cout << endl;
        cout << "Enter 1 or 2: ";
        cin >> mapping;

        cout << endl;

        if (choice == "1" || choice == "RSA") {
            string action;
            cout << "PRESS: E to Encrypt or D to Decrypt: ";
            cin >> action;

            if (action == "E" || action == "e") {
                // Encrypting using RSA
                int p, q, e, d, n;
                do {
                    cout << "Enter a prime number for p: ";
                    cin >> p;
                    if (!is_prime(p)) cout << "p is not a prime number. Try again.\n";
                } while (!is_prime(p));

                do {
                    cout << "Enter a prime number for q (different from p): ";
                    cin >> q;
                    if (!is_prime(q) || q == p) cout << "q must be a different prime number. Try again.\n";
                } while (!is_prime(q) || q == p);

                // Compute n and m
                n = p * q;
                int m = (p - 1) * (q - 1);

                // List valid values for e
                cout << "Prime numbers < " << n << " (valid values for e): ";
                for (int i = 2; i < m; i++) {
                    if (is_prime(i) && gcd(i, m) == 1) {
                        cout << i << " ";
                    }
                }

                cout << endl;

                // User selects a valid e
                do {
                    cout << "Select a value for e from the above numbers: ";
                    cin >> e;
                    if (gcd(e, m) != 1) {
                        cout << "e and m are not co-prime. Choose another value.\n";
                    }
                } while (gcd(e, m) != 1);

                // Compute d using modular inverse
                d = mod_inverse(e, m);

                cout << "Public Key: (e = " << e << ", n = " << n << ")" << endl;
                cout << "Private Key: (d = " << d << ", n = " << n << ")" << endl;

                // Encrypt the message
                string message;
                cout << "Enter a message to encrypt (uppercase letters only): ";
                cin >> message;

                vector<int> encrypted_message = encrypt_message(message, e, n, mapping);

                // Display encrypted message
                cout << "Encrypted Message (Numbers): ";
                for (int num : encrypted_message) {
                    cout << num << " ";
                }

                cout << endl;

            } else if (action == "D" || action == "d") {
                // Decrypting using RSA
                int d, n;
                cout << "Enter the value for d (private key): ";
                cin >> d;
                cout << "Enter the value for n (public key n): ";
                cin >> n;

                // Enter encrypted message
                vector<int> encrypted_message;
                int message_length;

                cout << "Enter the number of characters in the encrypted message: ";
                cin >> message_length;

                cout << "Enter the encrypted message (numbers separated by space): ";
                for (int i = 0; i < message_length; i++) {
                    int num;
                    cin >> num;
                    encrypted_message.push_back(num);
                }

                // Decrypt the message
                string decrypted_message = decrypt_message(encrypted_message, d, n, mapping);

                // Display decrypted message
                cout << "Decrypted Message: " << decrypted_message << endl;
            }

        } else if (choice == "2" || choice == "Caesar") {
            string action;
            cout << "PRESS: E to Encrypt or D to Decrypt: ";
            cin >> action;

            if (action == "E" || action == "e") {
                string message;
                int shift;
                cout << "Enter message to encrypt: ";
                cin >> message;
                cout << "Enter shift value: ";
                cin >> shift;
                cout << "Encrypted message: " << caesar_encrypt(message, shift, mapping) << endl;
            } else if (action == "D" || action == "d") {
                string message;
                int shift;
                cout << "Enter message to decrypt: ";
                cin >> message;
                cout << "Enter shift value: ";
                cin >> shift;
                cout << "Decrypted message: " << caesar_decrypt(message, shift, mapping) << endl;
            }

        } else if (choice == "3" || choice == "Transposion") {
            string action;
            cout << "PRESS: E to Encrypt or D to Decrypt: ";
            cin >> action;

            if (action == "E" || action == "e") {
                string message;
                int key;
                cout << "Enter message to encrypt: ";
                cin >> message;
                cout << "Enter key: ";
                cin >> key;
                cout << "Encrypted message: " << transposition_encrypt(message, key) << endl;
            } else if (action == "D" || action == "d") {
                string message;
                int key;
                cout << "Enter message to decrypt: ";
                cin >> message;
                cout << "Enter key: ";
                cin >> key;
                cout << "Decrypted message: " << transposition_decrypt(message, key) << endl;
            }

        } else if (choice == "4" || choice == "Railfence" || choice == "Rail Fence") {
            string action;
            cout << "PRESS: E to Encrypt or D to Decrypt: ";
            cin >> action;

            if (action == "E" || action == "e") {
                string message;
                int key;
                cout << "Enter message to encrypt: ";
                cin >> message;
                cout << "Enter key: ";
                cin >> key;
                cout << "Encrypted message: " << rail_fence_encrypt(message, key) << endl;
            } else if (action == "D" || action == "d") {
                string message;
                int key;
                cout << "Enter message to decrypt: ";
                cin >> message;
                cout << "Enter key: ";
                cin >> key;
                cout << "Decrypted message: " << rail_fence_decrypt(message, key) << endl;
            }

        } 

        else if (choice == "5" || choice == "Brute Force Caesar") {
            // Brute Force Caesar decryption
            string encrypted_message;
            cout << "Enter the encrypted message (Caesar Cipher): ";
            cin.ignore();  // Clear the buffer
            getline(cin, encrypted_message);  // Read the entire line

            vector<string> decrypted_messages = brute_force_caesar_decrypt(encrypted_message, mapping);

            cout << "Brute Force Decryption Results:" << endl;
            for (int i = 0; i < decrypted_messages.size(); i++) {
                cout << "Shift " << i + 1 << ": " << decrypted_messages[i] << endl;
            }
        }

        
        else {
            cout << "Invalid choice, please try again." << endl;
        }

        char repeat;
        cout << endl;
        cout << "Do you want to perform another action? (y/n): ";
        cin >> repeat;
        running = (repeat == 'y' || repeat == 'Y');
    }

    cout << "\033[32m" << endl;

    return 0;
}
