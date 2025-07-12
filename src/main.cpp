#include <iostream>
#include <gmpxx.h>
#include <cstdlib>  // For system("pause")
#include "rsaBasic.h"
#include "caesar.h"
#include "transposition.h"
#include "railfence.h"
#include "b_caesar.h"
#include "vigenere.h"
#include "columnar_transposition.h"
#include "caesar_polyalphabetic.h"
#include "converter.h"
#include "modulus.h"
#include "hexadecimal.h"
#include "hexconversion.h"
#include "caesar_sequence.h"
#include "CharacterCounter.h" 
#include "md5_easy.h"
#include "md5_reverse.h"
#include "sha1_easy.h"
#include "sha256_easy.h"
#include "HashIdentifier.h"
#include "hash_api_reverse.h"
#include "hash_reverseAPI.h"
#include "hill_cipher.h"
#include "filedialog.h"
#include "DiffieHellman.h"
#include "diffieHellmanMITM.h"
#include <string>
#include <filesystem>

#include <thread>   // For sleep
#include <chrono>   // For time units
#include <random>
#include <limits>


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

//CTF
#include <cryptlib.h>
#include <integer.h>
#include <string>
#include <limits>
#include "steganography.h"
#include "substitution.h"
#include "substitution_bruteforce.h"
#include "substitution_frequence.h"
#include "factorDB.h"
#include "rsaCTF.h"
#include "rsaCTFKEY.h"
#include "rsaCTFen.h"
#include "rot13CTF.h"
#include "framework.h"
#include "decrypt_square_rsa.h"
#include "decrypt_prime_rsa.h"
#include "rsa_solver.h"
#include "rsa_low_exp.h"
#include "multi_prime_rsa.h"
#include "weirderRSA.h"
#include "weird_rsa2.h"
#include "complex_rsa.h"
#include "hex_to_decimal.h"
#include "srsa_solver.h"
#include "rsa_non_coprime.h"
#include "base64CTF.h"
#include "dachshundAttack.h"
#include "rsa_trick.h"
#include "mono_substitution.h"
#include "morse_decoder.h"
#include "RSADecoder.h"
#include "triple_rsa_solver.h"
#include "MiniRSA.h"
#include "hastad.h"
#include "pollard.h"
#include "PollardSolver.h"
#include "hash_utils.h"

#include <sstream>   // for stringstream

using namespace std;
using CryptoPP::Integer;

namespace fs = std::filesystem;

void check_required_files() {
    std::vector<std::string> required = {
        "wordlists/wordlist.txt",
    };

    for (const auto& path : required) {
        if (!fs::exists(path)) {
            std::cerr << RED << "[!]" << RESET << " Missing required file: " << path << std::endl;
            std::cerr << CYAN << "    -> Please re-download the full release or clone the repository with all files." << RESET << std::endl;
            exit(1);
        }
    }
}

#ifdef _WIN32
#include <windows.h>
void EnableVirtualTerminalProcessing() {
    HANDLE hOut = GetStdHandle(STD_OUTPUT_HANDLE);
    if (hOut == INVALID_HANDLE_VALUE) return;

    DWORD dwMode = 0;
    if (!GetConsoleMode(hOut, &dwMode)) return;

    dwMode |= ENABLE_VIRTUAL_TERMINAL_PROCESSING;
    SetConsoleMode(hOut, dwMode);
}
#else
// On Linux / WSL, this is a no-op
void EnableVirtualTerminalProcessing() {}
#endif

void displayLogo() {
    cout << RED;
    cout                  << "   SSS   OOOO  K  K  OOOO  N   N   AAA   L   Y   Y  SSS   I   SSS   "          << endl;
    cout                  << "  S      O  O  K K   O  O  NN  N  A   A  L    Y Y  S      I  S      " << RESET << endl;
    cout << WHITE         << "   BREAK SECURE COMMUNICATIONS WITH OR WITHOUT THE DECRIPTION KEY!  " << RESET << endl;
    cout << RED           << "      S  O  O  K K   O  O  N  NN  A   A  L     Y       S  I      S  " << endl;
    cout                  << "   SSS   OOOO  K  K  OOOO  N   N  A   A  LLLL  Y    SSS   I   SSS   " << endl;
    cout << RESET;
}

void displayLogo2(){
    std::cout << RED << RED << R"(            
            __  __
           |  \/  |
            |    | 
           |__/\__|
      
)" << RESET << std::endl;
}

void displayLogo3() {
    const std::string logo[] = {
        "             .__.                      __              .__        ",
        "  __________ |  | ______  _____  ____ |  |  _ __  _____|__| ______",
        " |  ___| _  ||  || | _  ||  _  ||__  ||  | | |  ||  ___|  ||  ___/",
        " |___ | |_| ||    | |_| || | | || __ ||  |_|__  ||___ ||  ||___ | ",
        " ______|____||__|__|____||_| |_||____/|____/ ___|______|__/______|"
    };

    const std::string glitchChars = ".";

    auto glitchLine = [&](const std::string& line, double glitchChance = 0.1) -> std::string {
        static std::random_device rd;
        static std::mt19937 rng(rd());
        static std::uniform_real_distribution<> chance(0.0, 1.0);
        static std::uniform_int_distribution<> glitchChar(0, glitchChars.size() - 1);

        std::string glitched = line;
        for (char& c : glitched) {
            if (c != ' ' && chance(rng) < glitchChance) {
                c = glitchChars[glitchChar(rng)];
            }
        }
        return glitched;
    };

    // Glitch animation
    const int frames = 20;
    const int delay_ms = 100;

    for (int i = 0; i < frames; ++i) {
        std::cout << CLEAR << GREEN;
        for (const auto& line : logo) {
            std::cout << glitchLine(line, 0.1 + 0.05 * (frames - i) / frames) << std::endl;
        }
        std::cout << RESET;
        std::this_thread::sleep_for(std::chrono::milliseconds(delay_ms));
    }

    // Final clean logo
    std::cout << CLEAR << GREEN;
    for (const auto& line : logo) {
        std::cout << line << std::endl;
    }
    std::cout << RESET;
}

void pauseConsole() {
    cout << "Press Enter to continue...";
    cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
    cin.get();
}

void displayHelp() {
    // Stage 1: Show RSA Algorithm
    cout << BLUE << "\n___________________________ " << GREEN << "Help Menu" << RESET << BLUE << " ___________________________\n"<< RESET;
    cout << endl;
    pauseConsole();
    cout << endl;
    cout << "     " << GREEN << "RSA (Rivest Shamir Adleman) Algorithm" << RESET << "\n";
    cout << endl;
    cout << "     RSA is a public-key encryption algorithm that uses two keys\n";
    cout << "     A public key for encryption and a private key for decryption.\n";
    cout << endl; 
    cout << "     Choose p = 3 and q = 11\n";
    cout << endl;
    cout << "     Compute n = p * q\n";
    cout << "               = 3 * 11\n"; 
    cout << "               = 33\n";
    cout << endl;
    cout << "     Compute m = (p - 1) * (q - 1)\n";
    cout << "               = (3 - 1) * (11 - 1)\n";
    cout << "               = 2 * 10\n";
    cout << "               = 20\n";
    cout << endl;
    pauseConsole();
    cout << endl;
    cout << "     Prime numbers < n (33) = 2,3,5,7,11,13,17,19,23,29,31\n";
    cout << "     Valid prime numbers to represent e = 3,7,11,13,17,19,23,31\n";
    cout << endl;
    cout << "     d = ed-1/m, reminder =0\n";
    cout << "       = (7)(3)-1/20\n";
    cout << "       = 21-1/20\n";
    cout << "       = 20/20\n";
    cout << "       = 1\n";
    cout << endl;
    cout << "       Therefore d = 3\n";
    cout << endl;
    cout << "       message (m) = cipher (c) ^ d mod n\n";
    cout << "       cipher (c) = message (m) ^ e mod n\n";
    cout << endl;
    cout << "       message = 2\n";
    cout << endl;
    pauseConsole();
    cout << endl;
    cout << "       c = m ^ e mod n\n";
    cout << "         = 2 ^ 7 mod 33\n";
    cout << "         = 128 mod 33\n";
    cout << "         = 128/33\n";
    cout << "         = 3.87\n";
    cout << "         = 3 * 33\n";
    cout << "         = 99\n";
    cout << "         = 128 - 99\n";
    cout << "         = 29\n";
    cout << endl;
    cout << "       m = c ^ d mod n\n";
    cout << "         = 29 ^ 3 mod 33\n";
    cout << "         = 24389 mod 33\n";
    cout << "         = 24389/33\n";
    cout << "         = 739.06\n";
    cout << "         = 739 * 33\n";
    cout << "         = 24387\n";
    cout << "         = 24389 - 24387\n";
    cout << "         = 2\n";
    cout << endl;
    pauseConsole();
    cout << endl;

    // Stage 2: Show Caesar Cipher
    cout << "     " GREEN << "Caesar Cipher" RESET << "\n";
    cout << endl;
    cout << "     A substitution cipher where each letter of the plaintext is shifted by\n";
    cout << "     a fixed number.\n";
    cout << endl;
    cout << "     1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26\n";
    cout << "     A B C D E F G H I J  K  L  M  N  O  P  Q  R  S  T  U  V  W  X  Y  Z\n";
    cout << "     D E F G H I J K L M  N  O  P  Q  R  S  T  U  V  W  X  Y  Z  A  B  C\n";
    cout << endl;
    cout << "     Example: Plaintext = HELLO, Shift = 3, Ciphertext = KHOOR\n";
    cout << endl;

    pauseConsole();

    // Stage 2.1: Show Caesar Brute Force
    cout << endl;
    cout << "     " << GREEN << "Caesar Brute Force" << RESET << "\n";
    cout << endl;
    cout << "     Shift 01: B C D E F G H I J K L M N O P Q R S T U V W X Y Z A\n";
    cout << "     Shift 02: C D E F G H I J K L M N O P Q R S T U V W X Y Z A B\n";
    cout << "     Shift 03: D E F G H I J K L M N O P Q R S T U V W X Y Z A B C\n";
    cout << "     Shift 04: E F G H I J K L M N O P Q R S T U V W X Y Z A B C D\n";
    cout << "     Shift 05: F G H I J K L M N O P Q R S T U V W X Y Z A B C D E\n";
    cout << "     Shift 06: G H I J K L M N O P Q R S T U V W X Y Z A B C D E F\n";
    cout << "     Shift 07: H I J K L M N O P Q R S T U V W X Y Z A B C D E F G\n";
    cout << "     Shift 08: I J K L M N O P Q R S T U V W X Y Z A B C D E F G H\n";
    cout << "     Shift 09: J K L M N O P Q R S T U V W X Y Z A B C D E F G H I\n";
    cout << "     Shift 10: K L M N O P Q R S T U V W X Y Z A B C D E F G H I J\n";
    cout << "     Shift 11: L M N O P Q R S T U V W X Y Z A B C D E F G H I J K\n";
    cout << "     Shift 12: M N O P Q R S T U V W X Y Z A B C D E F G H I J K L\n";
    cout << "     Shift 13: N O P Q R S T U V W X Y Z A B C D E F G H I J K L M\n";
    cout << "     Shift 14: O P Q R S T U V W X Y Z A B C D E F G H I J K L M N\n";
    cout << "     Shift 15: P Q R S T U V W X Y Z A B C D E F G H I J K L M N O\n";
    cout << "     Shift 16: Q R S T U V W X Y Z A B C D E F G H I J K L M N O P\n";
    cout << "     Shift 17: R S T U V W X Y Z A B C D E F G H I J K L M N O P Q\n";
    cout << "     Shift 18: S T U V W X Y Z A B C D E F G H I J K L M N O P Q R\n";
    cout << "     Shift 19: T U V W X Y Z A B C D E F G H I J K L M N O P Q R S\n";
    cout << "     Shift 20: U V W X Y Z A B C D E F G H I J K L M N O P Q R S T\n";
    cout << "     Shift 21: V W X Y Z A B C D E F G H I J K L M N O P Q R S T U\n";
    cout << "     Shift 22: W X Y Z A B C D E F G H I J K L M N O P Q R S T U V\n";
    cout << "     Shift 23: X Y Z A B C D E F G H I J K L M N O P Q R S T U V W\n";
    cout << "     Shift 24: Y Z A B C D E F G H I J K L M N O P Q R S T U V W X\n";
    cout << "     Shift 25: Z A B C D E F G H I J K L M N O P Q R S T U V W X Y\n";
    cout << endl;

    pauseConsole();

    // Stage 2.2: Show Caesar Polyalphabetic Cipher
    cout << endl;
    cout << "     " << GREEN << "Caesar Polyalphabetic Cipher" << RESET << "\n";
    cout << endl;
    cout << "     A polyalphabetic cipher using multiple Caesar ciphers based on a keyword.\n";
    cout << endl;
    cout << "     Example   : Plaintext = WENEEDMORESUPPLIESFAST, Keyword = MEC\n";
    cout << endl;
    cout << "     Keyword   : M E C M E C M E C M E C M E C M E C M E C M\n";
    cout << "     Plaintext : W E N E E D M O R E S U P P L I E S F A S T\n";
    cout << "     Ciphertext: I I P Q I F Y S T Q W W B T N U I U R E U F\n";
    cout << endl;
    
    pauseConsole();

    // Stage 3: Show Vigenere Cipher
    cout << endl;
    cout << "     " << GREEN << "Vigenere Cipher" << RESET << "\n";
    cout << endl;
    cout << "     A polyalphabetic cipher that uses a keyword to shift letters.\n";
    cout << endl;
    cout << "     Example   : Plaintext = ATTACKATDAWN, Keyword = LEMON\n";
    cout << endl;
    cout << "     Plaintext : ATTACKATDAWN\n";
    cout << "     Key       : LEMONLEMONLE\n";
    cout << "     Ciphertext: LXFOPVEFRNHR\n";
    cout << endl;

    pauseConsole();

    // Stage 4: Show Transposition Cipher
    cout << endl;
    cout << "    " << GREEN << "Transposition Cipher" << RESET << "\n";
    cout << endl;
    cout << "    A transposition cipher rearranges the letters of the plaintext.\n";
    cout << endl;
    cout << "    Example: Plaintext = HELLO, Rearranged = LOHEL\n";
    cout << endl;

    pauseConsole();

    // Stage 4.1: Show Columnar Transposition Cipher
    cout << endl;
    cout << "     " << GREEN << "Columnar Transposition Cipher" << RESET << "\n";
    cout << endl;
    cout << "     A transposition cipher where the plaintext is written in a grid and\n";
    cout << "     rearranged by key.\n";
    cout << endl;
    cout << "     Example: Plaintext = WEAREDISCOVEREDFLEEATONCE, Key = ZEBRAS\n";
    cout << endl;
    cout << "     6 3 2 4 1 5\n";
    cout << "     W E A R E D\n";
    cout << "     I S C O V E\n";
    cout << "     R E D F L E\n";
    cout << "     E A T O N C\n"; 
    cout << "     E Q K J E U\n";
    cout << endl;
    cout << "     Ciphertext: EVLNEACDTKESEAQROFOJDEECUWIREE\n";
    cout << endl;

    pauseConsole();

    // Stage 4.2: Show Rail Fence Cipher
    cout << endl;
    cout << "     " << GREEN << "Rail Fence Cipher" << RESET << "\n";
    cout << endl;
    cout << "     A transposition cipher where the message is written in a zigzag pattern.\n";
    cout << endl;
    cout << "     Example: Plaintext = WEAREDISCOVEREDFLEEATONCE, Key = 3\n";
    cout << endl;
    cout << "     W . . . E . . . C . . . R . . . L . . . T . . . E\n";
    cout << "     . E . R . D . S . O . E . E . F . E . A . O . C .\n";
    cout << "     . . A . . . I . . . V . . . D . . . E . . . N . .\n";
    cout << endl;
    cout << "     Cipher = WECRLTEERDSOEEFEAOCAIVDEN\n \n";
    cout << endl;

    pauseConsole();
    cout << endl;
    cout << BLUE << "_________________________________________________________________\n" << RESET;
}

void about(){
    cout << BLUE << "\n_____________________________ " << GREEN << "About" << RESET << BLUE << " _____________________________\n"<< RESET;
    cout << endl;
    cout << "sokonalysis from the word Cryptanalysis is a Cryptographic tool\n"; 
    cout << "developed by Soko James and it seeks to decrypt encrypted\n"; 
    cout << "messages or break cryptographic systems without knowing the\n";
    cout << "secret key.\n";
    cout << endl;
    pauseConsole();
    cout << endl;
    cout << GREEN << "Follow us on:\n" << RESET;
    cout << BLUE << "Facebook" << RESET ": https://web.facebook.com/kceey.dc.5\n";
    cout << "GitHub  : https://github.com/SokoJames\n";
    cout << WHITE << "You" << RESET << RED << "Tube" << RESET << " : https://www.youtube.com/@s0k0j4m3s\n";
    cout << "Medium  : https://medium.com/@s0k0j4m3s\n";
    cout << endl;
    pauseConsole();
    cout << endl;
    cout << GREEN << "Download the latest sokonalysis version here\n" << RESET;
    cout << "https://github.com/SokoJames/sokonalysis\n";
    cout << endl;
    pauseConsole();
    cout << endl;
    cout << GREEN << "Contact us on \n" RESET;
    cout << GREEN << "WhatsApp   " << RESET << ": +260969209404\n";
    cout << "Direct call: +260774713037\n";
    cout << RED << "E" << RESET << ORANGE << "m" << RESET << YELLOW << "a" << RESET << GREEN << "i" << RESET << BLUE << "l" << RESET << "      : s0k0j4m3s@gmail.com\n";
    cout << BLUE << "_________________________________________________________________\n" << RESET;
    cout << endl;
    pauseConsole();
}


int main() {
    EnableVirtualTerminalProcessing();
    string choice;
    bool running = true;

    cout << endl;

    while (running) {
        cout << endl;
        displayLogo3();

        cout << endl;
        cout << CYAN  << "                  sokonalysis created by Soko James                      " << RESET << endl;
        cout << WHITE << "                       Last update 08 July 2025                           " << RESET << endl;
        cout << endl;
        cout << BLUE << "\n_____________________ " << GREEN << "SOKONALYSIS TOOL MENU" << RESET << BLUE << " _____________________\n"<< RESET;
        cout << endl;
        cout << YELLOW << "[1] " << RESET << "Symmetric Algorithms " << YELLOW << "            [5] " << RESET << "Advanced Cryptography " << endl;
        cout << YELLOW << "[2] " << RESET << "Asymmetric Algorithms" << YELLOW << "            [6] " << RESET << "Capture The Flag (CTF)" << endl;
        cout << YELLOW << "[3] " << RESET << "Hashing Algoritms    " << YELLOW << "            [7] " << RESET << "About"                  << endl;
        cout << YELLOW << "[4] " << RESET << "Other Algorithms     " << YELLOW << "            [8] " << RESET << "Help"                   << endl;
        cout << BLUE << "_________________________________________________________________\n" << RESET;
        cout << endl;
        cout << YELLOW << "[>] " << RESET<< "Enter your choice: ";
        cin >> choice;

        cout << endl;

        if (choice == "8" || choice == "08" || choice == "Help" || choice == "HELP") {
            displayHelp();  // Display the help menu when the user selects "9"
            continue;  // Skip the rest of the loop and show the menu again
        }

        else if (choice == "7" || choice == "07" || choice == "About" || choice == "about" || choice == "ABOUT"){
            about();
            continue;
        }

        cout << endl;

        if (choice == "1" || choice == "01" || choice == "Symetric" || choice == "symetric"){
            string sym_choice;
            cout << endl;
            cout << BLUE << "______________________" << RESET<< GREEN << " Symmetric Algorithms "<< RESET << BLUE << " ____________________" << RESET << endl;
            cout << endl;
            cout << YELLOW << "[1]" << RESET << " Caesar Cipher" << endl;
            cout << YELLOW << "[2]" << RESET << " Transposition Cipher" << endl;
            cout << YELLOW << "[3]" << RESET << " Hill Cipher" << endl;
            cout << YELLOW << "[4]" << RESET << " Advanced Encryption Standard (AES)" << endl;
            cout << BLUE << "_________________________________________________________________\n" << RESET;
            cout << endl;
            cout << YELLOW << "[>] " << RESET<< "Select an algorithm: ";
            cin >> sym_choice;


            if (sym_choice == "1" || sym_choice == "01" || sym_choice == "Caesar") {
                string sub_choice;
                cout << endl;
                cout << BLUE << "______________________" << RESET<< GREEN << " Caesar Cipher Options "<< RESET << BLUE << " ___________________" << RESET << endl;
                cout << endl;
                cout << YELLOW << "[1]" << RESET << " Basic Shift Caesar" << endl;
                cout << YELLOW << "[2]" << RESET << " Brute Force Caesar" << endl;
                cout << YELLOW << "[3]" << RESET << " Polyalphabetic Caesar" << endl;
                cout << BLUE << "_________________________________________________________________\n" << RESET;
                cout << endl;
                cout << YELLOW << "[>] " << RESET<< "Select an algorithm: ";
                cin >> sub_choice;
                cout << endl;
        
                if (sub_choice == "1" || sub_choice == "01" || sub_choice == "Caesar") {
                    // Ask the user for the shift mapping style
                    int mapping;
                    cout << endl;

                    cout << BLUE << "__________" << RESET<< GREEN << " Select the letter-to-number mapping style "<< RESET << BLUE << "____________" << RESET << endl;
                    cout << endl;
                    cout << YELLOW << "[1]" << RESET << " A=1, B=2, ..., Z=26" << endl;
                    cout << YELLOW << "[2]" << RESET << " A=0, B=1, ..., Z=25" << endl;
                    cout << BLUE << "_________________________________________________________________\n" << RESET;
                    cout << endl;
                    cout << YELLOW << "[>] " << RESET<< "Enter 1 or 2: ";
                    cin >> mapping;
                    cout << endl;

                    string action;
                    cout << YELLOW << "[>] " << RESET<< "PRESS: " << RED << "E " << RESET<< "to Encrypt or " << GREEN << "D " << RESET << "to Decrypt: ";
                    cin >> action;

                    if (action == "E" || action == "e") {
                        string message;
                        int shift;

                        cout << YELLOW << "[>] " << RESET<< "Enter message to encrypt: ";
                        cin >> message;
                        cout << YELLOW << "[>] " << RESET<< "Enter shift value: ";
                        cin >> shift;

                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                        cout << endl;
                        cout << RED << "[+] " RESET << "Encrypted message: " << RED << caesar_encrypt(message, shift, mapping) << RESET << endl;
                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                    } 
            
                    else if (action == "D" || action == "d") {
                        string message;
                        int shift;

                        cout << YELLOW << "[>] " << RESET<< "Enter message to decrypt: ";
                        cin >> message;

                        cout << YELLOW << "[>] " << RESET<< "Enter shift value: ";
                        cin >> shift;

                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                        cout << endl;
                        cout << GREEN << "[-] " << RESET << "Decrypted message: " << GREEN << caesar_decrypt(message, shift, mapping) << RESET << endl;
                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                    }

                    else {
                            cout << endl;
                            cout << RED << "[x] " << RESET << "Invalid Option Selected" << endl;
                            cout << endl;
                    }
                } 
        
                else if (sub_choice == "2" || sub_choice == "02" || sub_choice == "Brute Force Caesar") {
                    // Ask the user for the shift mapping style
                    int mapping;
                    cout << endl;

                    cout << BLUE << "__________" << RESET<< GREEN << " Select the letter-to-number mapping style "<< RESET << BLUE << "____________" << RESET << endl;
                    cout << endl;
                    cout << YELLOW << "[1]" << RESET << " A=1, B=2, ..., Z=26" << endl;
                    cout << YELLOW << "[2]" << RESET << " A=0, B=1, ..., Z=25" << endl;
                    cout << BLUE << "_________________________________________________________________\n" << RESET;
                    cout << endl;
                    cout << YELLOW << "[>] " << RESET<< "Enter 1 or 2: ";
                    cin >> mapping;
                    cout << endl;


                    // Brute Force Caesar decryption
                    string encrypted_message;
                    cout << YELLOW << "[>] " << RESET<< "Enter the encrypted message (Caesar Cipher): ";
                    cin.ignore();  // Clear the buffer
                    getline(cin, encrypted_message);  // Read the entire line

                    vector<string> decrypted_messages = brute_force_caesar_decrypt(encrypted_message, mapping);

                    cout << endl;

                    for (int i = 0; i < decrypted_messages.size(); i++) {
                        cout << endl;
                        pauseConsole();
                        cout << endl;

                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                        cout << endl;
                        cout << GREEN << "[-] " << RESET << "Shift " << i + 1 << " Decrypted Results: " << GREEN << decrypted_messages[i] << RESET << endl;
                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                        cout << endl;
                    }
                }

                else if (sub_choice == "3" || sub_choice == "03" || sub_choice == "Caesar Polyalphabetic") {  // Caesar Polyalphabetic option
                    string poly_choice;
                    cout << endl;

                    cout << BLUE << "_____________" << RESET<< GREEN << " Polyalphabetic Caesar Cipher Options "<< RESET << BLUE << "______________" << RESET << endl;
                    cout << endl;
                    cout << YELLOW << "[1]" << RESET << " Polyalphabetic Cipher (keyword-based)" << endl;
                    cout << YELLOW << "[2]" << RESET << " Vigenere Cipher (keyword-based)" << endl;
                    cout << YELLOW << "[3]" << RESET << " Polyaphabetic Cipher (sequence-based)" << endl;
                    cout << BLUE << "_________________________________________________________________\n" << RESET;
                    cout << endl;
                    cout << YELLOW << "[>] " << RESET<< "Select an algorithm: ";
                    cin >> poly_choice;

                    if (poly_choice == "1" || poly_choice == "01" || poly_choice == "Basic" || poly_choice == "basic"){   
                        // Ask the user for the shift mapping style
                        int mapping;
                        cout << endl;

                        cout << BLUE << "__________" << RESET<< GREEN << " Select the letter-to-number mapping style "<< RESET << BLUE << "____________" << RESET << endl;
                        cout << endl;
                        cout << YELLOW << "[1]" << RESET << " A=1, B=2, ..., Z=26" << endl;
                        cout << YELLOW << "[2]" << RESET << " A=0, B=1, ..., Z=25" << endl;
                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                        cout << endl;
                        cout << YELLOW << "[>] " << RESET<< "Enter 1 or 2: ";
                        cin >> mapping;
                        cout << endl;


                        string action;
                        cout << YELLOW << "[>] " << RESET<< "PRESS: " << RED << "E " << RESET<< "to Encrypt or " << GREEN << "D " << RESET << "to Decrypt: ";
                        cin >> action;

                        if (action == "E" || action == "e") {
                            string message, keyword;

                            cout << YELLOW << "[>] " << RESET<< "Enter message to encrypt: ";
                            cin >> message;

                            cout << YELLOW << "[>] " << RESET<< "Enter keyword: ";
                            cin >> keyword;

                            cout << BLUE << "_________________________________________________________________\n" << RESET;
                            cout << endl;
                            cout << RED << "[+] " RESET << "Encrypted message: " << RED << caesar_polyalphabetic_encrypt(message, keyword, mapping) << RESET << endl;
                            cout << BLUE << "_________________________________________________________________\n" << RESET;
                        } 
            
                        else if (action == "D" || action == "d") {
                            string message, keyword;

                            cout << YELLOW << "[>] " << RESET<< "Enter message to decrypt: ";
                            cin >> message;

                            cout << YELLOW << "[>] " << RESET<< "Enter keyword: ";
                            cin >> keyword;

                            cout << BLUE << "_________________________________________________________________\n" << RESET;
                            cout << endl;
                            cout << GREEN << "[-] " << RESET << "Decrypted message: " << GREEN << caesar_polyalphabetic_decrypt(message, keyword, mapping) << RESET << endl;
                            cout << BLUE << "_________________________________________________________________\n" << RESET;
                        }

                        else {
                            cout << endl;
                            cout << RED << "[x] " << RESET << "Invalid Option Selected" << endl;
                            cout << endl;
                        }
                    } 

                    else if (poly_choice == "2" || poly_choice == "02" || poly_choice == "Vigenere") {
                        cout << endl;
                        string action;

                        cout << YELLOW << "[>] " << RESET<< "PRESS: " << RED << "E " << RESET<< "to Encrypt or " << GREEN << "D " << RESET << "to Decrypt: ";
                        cin >> action;
        
                        if (action == "E" || action == "e") {
                            string message, keyword;

                            cout << YELLOW << "[>] " << RESET<< "Enter message to encrypt (uppercase letters only): ";
                            cin >> message;

                            cout << YELLOW << "[>] " << RESET<< "Enter keyword (uppercase letters only): ";
                            cin >> keyword;
                
                            cout << BLUE << "_________________________________________________________________\n" << RESET;
                            cout << endl;
                            cout << RED << "[+] " RESET << "Encrypted message: " << RED << vigenere_encrypt(message, keyword) << RESET << endl;
                            cout << BLUE << "_________________________________________________________________\n" << RESET;
                        } 
            
                        else if (action == "D" || action == "d") {
                            string message, keyword;

                            cout << YELLOW << "[>] " << RESET<< "Enter message to decrypt (uppercase letters only): ";
                            cin >> message;

                            cout << YELLOW << "[>] " << RESET<< "Enter keyword (uppercase letters only): ";
                            cin >> keyword;
                
                            cout << BLUE << "_________________________________________________________________\n" << RESET;
                            cout << endl;
                            cout << GREEN << "[-] " << RESET << "Decrypted message: " << GREEN << vigenere_decrypt(message, keyword) << RESET << endl;
                            cout << BLUE << "_________________________________________________________________\n" << RESET;
                        }

                        else {
                            cout << endl;
                            cout << RED << "[x] " << RESET << "Invalid Option Selected" << endl;
                            cout << endl;
                        }

                    }

                    else if (poly_choice == "3" || poly_choice == "03" || poly_choice == "Polyalphabetic Sequence Cipher") {
                        string action;
                        cout << endl;

                        cout << YELLOW << "[>] " << RESET<< "PRESS: " << RED << "E " << RESET<< "to Encrypt or " << GREEN << "D " << RESET << "to Decrypt: ";
                        cin >> action;
        
                        int numKeys;
                        cout << YELLOW << "[>] " << RESET<< "Enter number of keys: ";
                        cin >> numKeys;
        
                        vector<int> shifts(numKeys);

                        for (int i = 0; i < numKeys; ++i) {
                            cout << YELLOW << "[>] " << RESET<< "Enter shift value for key " << i + 1 << ": ";
                            cin >> shifts[i];
                        }
        
                        int seqLen;
                        cout << YELLOW << "[>] " << RESET<< "Enter length of key sequence: ";
                        cin >> seqLen;
        
                        vector<int> sequence(seqLen);
                        cout << YELLOW << "[>] " << RESET<< "Enter the sequence (space-separated indices starting from 0): ";

                        for (int i = 0; i < seqLen; ++i) {
                            cin >> sequence[i];
                        }
        
                        cin.ignore(); // Clear buffer before reading text
        
                        string text;
                        cout << YELLOW << "[>] " << RESET<< "Enter the text: ";
                        getline(cin, text);
        
                        PolyCipher cipher(shifts, sequence);
        
                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                        cout << endl;

                        if (action == "E" || action == "e") {
                            cout << RED << "[+] " RESET << "Encrypted message: " << RED << cipher.encrypt(text) << RESET << endl;
                        } 
            
                        else if (action == "D" || action == "d") {
                            cout << GREEN << "[-] " << RESET << "Decrypted message: " << GREEN << cipher.decrypt(text) << RESET << endl;
                        } 
            
                        else {
                            cout << RED << "[x] " << RESET << "Invalid action selected." << endl;
                            cout << endl;
                        }
            
                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                    }
                    
                    else {
                        cout << endl;
                        cout << RED << "[x] " << RESET << "Invalid Option Selected" << endl;
                        cout << endl;
                    }
                }

                else {
                    cout << endl;
                    cout << RED << "[x] " << RESET << "Invalid Option Selected" << endl;
                    cout << endl;
                }
            }
        
            else if (sym_choice == "2" || sym_choice == "02" || sym_choice == "Transposition") {
                string sub_choice;
                cout << endl;

                cout << BLUE << "_________________" << RESET<< GREEN << " Transposition Cipher Options "<< RESET << BLUE << "__________________" << RESET << endl;
                cout << endl;
                cout << YELLOW << "[1]" << RESET << " Basic Transposition Cipher" << endl;
                cout << YELLOW << "[2]" << RESET << " Columnar Transposition Cipher" << endl;
                cout << YELLOW << "[3]" << RESET << " Rail Fence Cipher" << endl;
                cout << BLUE << "_________________________________________________________________\n" << RESET;
                cout << endl;
                cout << YELLOW << "[>] " << RESET<< "Select an algorithm: ";
                cin >> sub_choice;

                if (sub_choice == "1" || sub_choice == "01" || sub_choice == "Transposion") {
                    string action;
                    cout << endl;

                    cout << YELLOW << "[>] " << RESET<< "PRESS: " << RED << "E " << RESET<< "to Encrypt or " << GREEN << "D " << RESET << "to Decrypt: ";
                    cin >> action;

                    if (action == "E" || action == "e") {
                        string message;
                        int key;

                        cout << YELLOW << "[>] " << RESET<< "Enter message to encrypt: ";
                        cin >> message;

                        cout << YELLOW << "[>] " << RESET<< "Enter key (number): ";
                        cin >> key;

                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                        cout << endl;
                        cout << RED << "[+] " RESET << "Encrypted message: " << RED << transposition_encrypt(message, key) << RESET << endl;
                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                    } 
            
                    else if (action == "D" || action == "d") {
                        string message;
                        int key;

                        cout << YELLOW << "[>] " << RESET<< "Enter message to decrypt: ";
                        cin >> message;

                        cout << YELLOW << "[>] " << RESET<< "Enter key: ";
                        cin >> key;

                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                        cout << endl;
                        cout << GREEN << "[-] " << RESET << "Decrypted message: " << GREEN << transposition_decrypt(message, key) << RESET << endl;
                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                    }

                    else {
                            cout << endl;
                            cout << RED << "[x] " << RESET << "Invalid Option Selected" << endl;
                            cout << endl;
                    }
                } 
        
                else if (sub_choice == "2" || sub_choice == "02" || sub_choice == "Columnar Transposition") { // Columnar Transposition selection
                    string action;
                    cout << endl;

                    cout << YELLOW << "[>] " << RESET<< "PRESS: " << RED << "E " << RESET<< "to Encrypt or " << GREEN << "D " << RESET << "to Decrypt: ";
                    cin >> action;

                    // Prompt the user for the key
                    string key;

                    cout << YELLOW << "[>] " << RESET<< "Enter keyword: ";
                    cin >> key;

                    ColumnarTransposition cipher(key); // Use the entered key

                    if (action == "E" || action == "e") {
                        string message;

                        cout << YELLOW << "[>] " << RESET<< "Enter message to encrypt: ";
                        cin >> message;

                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                        cout << endl;
                        cout << RED << "[+] " RESET << "Encrypted message: " << RED << cipher.encrypt(message) << RESET << endl;
                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                    } 
            
                    else if (action == "D" || action == "d") {
                        string message;

                        cout << YELLOW << "[>] " << RESET<< "Enter message to decrypt: ";
                        cin >> message;

                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                        cout << endl;
                        cout << GREEN << "[-] " << RESET << "Decrypted message: " << GREEN << cipher.decrypt(message) << RESET << endl;
                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                    }

                    else {
                            cout << endl;
                            cout << RED << "[x] " << RESET << "Invalid Option Selected" << endl;
                            cout << endl;
                    }
                }

                else if (sub_choice == "3" || sub_choice == "03" || sub_choice == "Railfence" || sub_choice == "Rail Fence") {
                    string action;
                    cout << endl;

                    cout << YELLOW << "[>] " << RESET<< "PRESS: " << RED << "E " << RESET<< "to Encrypt or " << GREEN << "D " << RESET << "to Decrypt: ";
                    cin >> action;

                    if (action == "E" || action == "e") {
                        string message;
                        int key;

                        cout << YELLOW << "[>] " << RESET<< "Enter message to encrypt: ";
                        cin >> message;

                        cout << YELLOW << "[>] " << RESET<< "Enter number of rails: ";
                        cin >> key;

                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                        cout << endl;
                        cout << RED << "[+] " RESET << "Encrypted message: " << RED << rail_fence_encrypt(message, key) << RESET << endl;
                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                    } 
            
                    else if (action == "D" || action == "d") {
                        string message;
                        int key;

                        cout << YELLOW << "[>] " << RESET<< "Enter message to decrypt: ";
                        cin >> message;

                        cout << YELLOW << "[>] " << RESET<< "Enter number of rails: ";
                        cin >> key;

                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                        cout << endl;
                        cout << GREEN << "[-] " << RESET << "Decrypted message: " << GREEN << rail_fence_decrypt(message, key) << RESET << endl;
                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                    }

                    else {
                            cout << endl;
                            cout << RED << "[x] " << RESET << "Invalid Option Selected" << endl;
                            cout << endl;
                    }
                }
                
                else {
                    cout << endl;
                    cout << RED << "[x] " << RESET << "Invalid Option Selected" << endl;
                    cout << endl;
                }
            }

            else if (sym_choice == "3" || sym_choice == "03" || sym_choice == "Hill") {
                cout << endl;
                cout << RED<< "[!]" << RESET << " Currently not available" << endl;
            }

            else if (sym_choice == "4" || sym_choice == "04" || sym_choice == "AES" || sym_choice == "aes") {
                cout << endl;
                cout << RED<< "[!]" << RESET << " Currently not available" << endl;
            }

            else {
                cout << endl;
                cout << RED << "[x] " << RESET << "Invalid Option Selected" << endl;
                cout << endl;
            }
        }   
    
        else if (choice == "2" || choice == "Asymetric" || choice == "asymetric"){
            string asym_choice;
            cout << endl;

            cout << BLUE << "_____________________" << RESET<< GREEN << " Asymmetric Algorithms "<< RESET << BLUE << "_____________________" << RESET << endl;
            cout << endl;
            cout << YELLOW << "[1]" << RESET << " Rivest Shamir Adleman (RSA)" << endl;
            cout << YELLOW << "[2]" << RESET << " Diffie Hellman" << endl;
            cout << BLUE << "_________________________________________________________________\n" << RESET;
            cout << endl;
            cout << YELLOW << "[>] " << RESET<< "Select an algorithm: ";
            cin >> asym_choice;

            if (asym_choice == "1" || asym_choice == "01" || asym_choice == "RSA") {
                // Ask the user for the shift mapping style
                int mapping;
                cout << endl;

                cout << BLUE << "__________" << RESET<< GREEN << " Select the letter-to-number mapping style "<< RESET << BLUE << "____________" << RESET << endl;
                cout << endl;
                cout << YELLOW << "[1]" << RESET << " A=1, B=2, ..., Z=26" << endl;
                cout << YELLOW << "[2]" << RESET << " A=0, B=1, ..., Z=25" << endl;
                cout << BLUE << "_________________________________________________________________\n" << RESET;
                cout << endl;
                cout << YELLOW << "[>] " << RESET<< "Enter 1 or 2: ";
                cin >> mapping;
                cout << endl;


                string action;
                cout << endl;
                cout << YELLOW << "[>] " << RESET<< "PRESS: " << RED << "E " << RESET<< "to Encrypt or " << GREEN << "D " << RESET << "to Decrypt: ";
                cin >> action;

                if (action == "E" || action == "e") {
                    // Encrypting using RSA
                    int p, q, e, d, n;

                    do {
                        cout << YELLOW << "[>] " << RESET<< "Enter a prime number for p: ";
                        cin >> p;

                        if (!is_prime(p)){ 
                            cout << RED << "[x] " << RESET << "p is not a prime number. Try again.\n";
                            cout << endl;
                            displayLogo2();
                            cout << endl;
                        }
                    } while (!is_prime(p));

                    do {
                        cout << YELLOW << "[>] " << RESET<< "Enter a prime number for q (different from p): ";
                        cin >> q;

                        if (!is_prime(q) || q == p){ 
                            cout << RED << "[x] " << RESET << "q must be a prime number and different from p. Try again.\n";
                            cout << endl;
                            displayLogo2();
                            cout << endl;
                        }
                    } while (!is_prime(q) || q == p);

                    // Compute n and m
                    n = p * q;

                    int m = (p - 1) * (q - 1);

                    // List valid values for e
                    cout << CYAN << "[#] " RESET << "Prime numbers < " << n << " (valid values for e): ";

                    for (int i = 2; i < m; i++) {
                        if (is_prime(i) && gcd(i, m) == 1) {
                            cout << i << " ";
                        }
                    }

                    cout << endl;

                    // User selects a valid e
                    do {
                        cout << YELLOW << "[>] " << RESET<< "Select a value for e from the above numbers: ";
                        cin >> e;

                        if (gcd(e, m) != 1) {
                            cout << RED << "[x] " << RESET << "e and m are not co-prime. Choose another value.\n";
                            cout << endl;
                            displayLogo2();
                            cout << endl;
                        }

                    } while (gcd(e, m) != 1);

                    // Compute d using modular inverse
                    d = mod_inverse(e, m);

                    cout << CYAN << "[#] " RESET << "Public Key: " << RED << "(e = " << e << ", n = " << n << ")" << RESET << endl;
                    cout << CYAN << "[#] " RESET << "Private Key: " << GREEN << "(d = " << d << ", n = " << n << ")" << RESET << endl;

                    // Encrypt the message
                    string message;
                    cout << YELLOW << "[>] " << RESET<< "Enter a message to encrypt (uppercase letters only): ";
                    cin >> message;

                    vector<int> encrypted_message = encrypt_message(message, e, n, mapping);

                    // Display encrypted message
                    cout << BLUE << "_________________________________________________________________\n" << RESET;
                    cout << endl;
                    cout << RED << "[+] " RESET << "Encrypted Message (Numbers): ";

                    for (int num : encrypted_message) {
                        cout << RED << num << RESET << " ";
                    }

                    cout << endl;
                    cout << BLUE << "_________________________________________________________________\n" << RESET;
                } 
        
                else if (action == "D" || action == "d") {
                    // Decrypting using RSA
                    int d, n;

                    cout << YELLOW << "[>] " << RESET<< "Enter the value for d (" << GREEN << "private key" << RESET << "): ";
                    cin >> d;

                    cout << YELLOW << "[>] " << RESET<< "Enter the value for n (" << RED << "public key" << RESET << "): ";
                    cin >> n;

                    // Enter encrypted message
                    vector<int> encrypted_message;
                    int message_length;

                    cout << YELLOW << "[>] " << RESET<< "Enter the number of characters in the encrypted message: ";
                    cin >> message_length;

                    cout << YELLOW << "[>] " << RESET<< "Enter the encrypted message (numbers separated by space): ";

                    for (int i = 0; i < message_length; i++) {
                        int num;

                        cin >> num;

                        encrypted_message.push_back(num);
                    }

                    // Decrypt the message
                    string decrypted_message = decrypt_message(encrypted_message, d, n, mapping);

                    // Display decrypted message
                    cout << BLUE << "_________________________________________________________________\n" << RESET;
                    cout << endl;
                    cout << GREEN << "[-] " << RESET << "Decrypted Message: " << GREEN << decrypted_message << RESET << endl;
                    cout << BLUE << "_________________________________________________________________\n" << RESET;
                }

                else {
                    cout << endl;
                    cout << RED << "[x] " << RESET << "Invalid Option Selected" << endl;
                    cout << endl;
                }
            }

            else if (asym_choice == "02" || asym_choice == "2"){
                string diffie_choice;
                cout << endl;

                cout << BLUE << "____________________" << RESET<< GREEN << " Diffie Hellman Options "<< RESET << BLUE << "_____________________" << RESET << endl;
                cout << endl;
                cout << YELLOW << "[1]" << RESET << " Basic Operation" << endl;
                cout << YELLOW << "[2]" << RESET << " Man-In-The-Middle (MITM) Attack" << endl;
                cout << BLUE << "_________________________________________________________________\n" << RESET;
                cout << endl;
                cout << YELLOW << "[>] " << RESET<< "Select an option: ";
                cin >> diffie_choice;

                if (diffie_choice == "01" || diffie_choice == "1"){
                int p, g; // public values
                int a, b; // private secrets

                // Input public parameters
                std::cout << std::endl;
                std::cout << YELLOW << "[>]" << RESET << " Enter prime modulus (p): ";
                std::cin >> p;

                std::cout << YELLOW << "[>]" << RESET << " Enter primitive root modulo p (g): ";
                std::cin >> g;

                // Input secret values
                std::cout << YELLOW << "[>]" << RESET << " Enter private value a: ";
                std::cin >> a;

                std::cout << YELLOW << "[>]" << RESET << " Enter private value b: ";
                std::cin >> b;

                // Generate participants
                DiffieHellman userA(g, p, a);
                DiffieHellman userB(g, p, b);

                // Generate public keys
                int A = userA.generatePublicKey(); // A = g^a mod p
                int B = userB.generatePublicKey(); // B = g^b mod p

                // Exchange public keys and compute shared keys
                int sharedKeyA = userA.computeSharedKey(B); // s = B^a mod p
                int sharedKeyB = userB.computeSharedKey(A); // s = A^b mod p

                // Output results
                cout << endl;
                cout << RED << "Public Values"<< RESET << endl;
                std::cout << RED << "p" << RESET << " (modulus): " << RED << p << RESET << endl;
                std::cout << RED << "g" << RESET << " (base): " << RED << g << RESET << endl;

                cout << endl;
                cout << BLUE << ORANGE << "Public Keys"<< RESET << endl;
                std::cout << ORANGE << "A" << RESET << " = g^a mod p = " << ORANGE << A << RESET << endl;
                std::cout << ORANGE << "B" << RESET << " = g^b mod p = " << ORANGE << B << RESET << endl;
                
                cout << endl;
                cout << BLUE << GREEN << "Shared Key"<< RESET << endl;
                std::cout << "computed with " << ORANGE << "B" << RESET << "^a mod " << RED << "p" << RESET << ": " << GREEN << sharedKeyA << RESET << endl;
                std::cout << "computed with " << ORANGE << "A" << RESET << "^b mod " << RED << "p" << RESET << ": " << GREEN << sharedKeyB << RESET << endl;

                if (sharedKeyA == sharedKeyB) {
                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                        cout << endl;
                        std::cout << GREEN << "[-]" << RESET << " Shared symmetric key is " << GREEN << sharedKeyA << RESET << endl;
                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                } 
                
                else {
                        std::cout << RED << "[x]" << RESET << " Keys do not match" << endl;
                }
            }

            else if (diffie_choice == "02" || diffie_choice == "2"){
                long long p, g, A_pub, B_pub;

                cout << endl;
                cout << YELLOW << "[>]" << RESET << " Enter prime number (p): ";
                cin >> p;
                cout << YELLOW << "[>]" << RESET << " Enter primitive root (g): ";
                cin >> g;

                cout << YELLOW << "[>]" << RESET << " Enter intercepted public key from A: ";
                cin >> A_pub;
                cout << YELLOW << "[>]" << RESET << " Enter intercepted public key from B: ";
                cin >> B_pub;

                DiffieHellmanMITM mitm;
                mitm.simulate(g, p, A_pub, B_pub);
            }
            }
            
            else {
                cout << endl;
                cout << RED << "[x] " << RESET << "Invalid Option Selected" << endl;
                cout << endl;
            }
        }

        else if (choice == "3" || choice == "03" || choice == "Hashing" || choice == "hashing"){
            string hash_choice;
            cout << endl;
            cout << BLUE << "_______________________" << RESET<< GREEN << " Hashing Algorithms "<< RESET << BLUE << " _____________________" << RESET << endl;
            cout << endl;
            cout << YELLOW << "[1]" << RESET << " Message Digest 5 (MD5)" << endl;
            cout << YELLOW << "[2]" << RESET << " Secure Hash Algorithm (SHA)" << endl;
            cout << YELLOW << "[3]" << RESET << " Hash Identifier" << endl;
            cout << YELLOW << "[4]" << RESET << " Hash Reversor" << endl;
            cout << BLUE << "_________________________________________________________________\n" << RESET;
            cout << endl;
            cout << YELLOW << "[>] " << RESET<< "Select an algorithm: ";
            cin >> hash_choice;

            if (hash_choice == "1" || hash_choice == "01" || hash_choice == "MD5" || hash_choice == "md5"){
                string action;
                cout << endl;
                cout << YELLOW << "[>] " << RESET<< "PRESS: " << RED << "G " << RESET<< "to Generate a hash or " << GREEN << "R " << RESET << "to Reverse the hash: ";
                cin >> action;

                if (action == "G" || action == "g") {
                    string input;
                    cout << YELLOW << "[>] " << RESET << "Enter a string to hash: ";
                    cin.ignore(); // To clear any leftover newline character
                    getline(cin, input);

                    string md5_hash = generateMD5(input); // Call generateMD5 function
                    cout << BLUE << "_________________________________________________________________\n" << RESET;
                    cout << endl;
                    cout << RED << "[+] " << RESET <<"MD5 Hash: " << RED <<  md5_hash << RESET << endl;
                    cout << BLUE << "_________________________________________________________________\n" << RESET;
                }
                
                else if (action == "R" || action == "r") {
                    std::string inputHash;
                    std::cout << YELLOW << "[>] " << RESET << "Enter MD5 hash to reverse: ";
                    std::cin >> inputHash;
                
                    std::string method;
                    cout << endl;
                    cout << BLUE << "_____________________ " << GREEN << "Reversing  Method" << RESET << BLUE <<  " _________________________\n" << RESET;
                    cout << endl;
                    std::cout << YELLOW << "[1]" << RESET << " Use online browser\n";
                    std::cout << YELLOW << "[2]" << RESET << " Use local wordlist\n" << RESET;
                    std::cout << YELLOW << "[3]" << RESET << " Use online API\n";
                    cout << BLUE << "_________________________________________________________________\n" << RESET;
                    cout << endl;
                    std::cout << YELLOW << "[>] " << RESET << "Enter option: ";
                    std::cin >> method;
                    cout << endl;
                
                    if (method == "1") {
                        std::cout << GREEN << "[-] " << RESET << "Opening your browser..." << std::endl;
                        openDCodeWithHash(inputHash);
                    } 
                    
                    else if (method == "2") {
                        std::string wordlistPath = "wordlist.txt";
                        std::cout << ORANGE << "[?] " << RESET << "Searching local wordlist..." << std::endl;
                        std::string result = searchWordlist(inputHash, wordlistPath);
                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                        cout << endl;
                        std::cout << GREEN << "[-] " << RESET << "Result: " << GREEN <<  result << RESET << std::endl;
                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                    } 

                    else if (method == "3") {
                        std::string hashType = "md5"; // or dynamically detect it
                        std::cout << ORANGE << "[*] " << RESET << "Querying API..." << std::endl;
                        std::string result = reverseHashViaAPI(inputHash, hashType);
                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                        cout << endl;
                        std::cout << GREEN << "[-] " << RESET << "Result: " << GREEN << result << RESET << std::endl;
                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                    }

                    else {
                        std::cout << RED << "[!] Invalid method choice." << RESET << std::endl;
                    }
                }

                else {
                    cout << endl;
                    cout << RED << "[x] " << RESET << "Invalid Option Selected" << endl;
                    cout << endl;
                }
            }

            else if (hash_choice == "2" || hash_choice == "02" || hash_choice == "SHA" || hash_choice == "sha"){
                    string sha_choice;
                    cout << endl;
                    cout << BLUE << "__________________________" << RESET<< GREEN << " SHA Category "<< RESET << BLUE << " ________________________" << RESET << endl;
                    cout << endl;
                    cout << YELLOW << "[1]" << RESET << " SHA-1" << endl;
                    cout << YELLOW << "[2]" << RESET << " SHA-256" << endl;
                    cout << BLUE << "_________________________________________________________________\n" << RESET;
                    cout << endl;
                    cout << YELLOW << "[>] " << RESET<< "Select an algorithm: ";
                    cin >> sha_choice;

                    if (sha_choice == "1" || sha_choice == "01") {
                        string action;
                        cout << endl;
                        cout << YELLOW << "[>] " << RESET<< "PRESS: " << RED << "G " << RESET<< "to Generate a hash or " << GREEN << "R " << RESET << "to Reverse the hash: ";
                        cin >> action;
                    
                        if (action == "G" || action == "g") {
                            string input;
                            cout << YELLOW << "[>] " << RESET << "Enter a string to hash: ";
                            cin.ignore(); // Clear newline
                            getline(cin, input);
                    
                            string sha1_hash = sha1(input); // Call SHA-1 generator
                            cout << BLUE << "_________________________________________________________________\n" << RESET;
                            cout << endl;
                            cout << RED << "[+] " << RESET <<"SHA-1 Hash: " << RED << sha1_hash << RESET << endl;
                            cout << BLUE << "_________________________________________________________________\n" << RESET;
                        }
                    
                        else if (action == "R" || action == "r") {
                            std::string inputHash;
                            std::cout << YELLOW << "[>] " << RESET << "Enter SHA-1 hash to reverse: ";
                            std::cin >> inputHash;
                    
                            std::string method;
                            cout << endl;
                            cout << BLUE << "_____________________ " << GREEN << "Reversing  Method" << RESET << BLUE <<  " _________________________\n" << RESET;
                            cout << endl;
                            std::cout << YELLOW << "[1]" << RESET << " Use online browser\n";
                            std::cout << YELLOW << "[2]" << RESET << " Use local wordlist\n";
                            cout << BLUE << "_________________________________________________________________\n" << RESET;
                            cout << endl;
                            std::cout << YELLOW << "[>] " << RESET << "Enter option: ";
                            std::cin >> method;
                            cout << endl;
                    
                            if (method == "1") {
                                std::cout << GREEN << "[-] " << RESET << "Opening your browser..." << std::endl;
                                openSHA1OnlineLookup(inputHash);
                            } 
                            
                            else if (method == "2") {
                                std::string wordlistPath = "wordlist.txt"; // Reuse same wordlist
                                std::cout << ORANGE << "[?] " << RESET << "Searching local wordlist..." << std::endl;
                                std::string result = searchSHA1Wordlist(inputHash, wordlistPath);
                                cout << BLUE << "_________________________________________________________________\n" << RESET;
                                cout << endl;
                                std::cout << GREEN << "[-] " << RESET << "Result: " << GREEN << result << RESET << std::endl;
                                cout << BLUE << "_________________________________________________________________\n" << RESET;
                            } 
                            
                            else {
                                std::cout << RED << "[!] Invalid method choice." << RESET << std::endl;
                            }
                        } 

                        else {
                                cout << endl;
                                cout << RED << "[x] " << RESET << "Invalid Option Selected" << endl;
                                cout << endl;
                        }
                    }

                    else if (sha_choice == "2" || sha_choice == "02" || sha_choice == "256") {
                        string action;
                        cout << endl;
                        cout << YELLOW << "[>] " << RESET << "PRESS: " << RED << "G " << RESET << "to Generate a hash or "
                             << GREEN << "R " << RESET << "to Reverse the hash: ";
                        cin >> action;
                    
                        if (action == "G" || action == "g") {
                            string input;
                            cout << YELLOW << "[>] " << RESET << "Enter a string to hash: ";
                            cin.ignore();
                            getline(cin, input);
                    
                            string sha_hash = sha256(input);
                            cout << BLUE << "_________________________________________________________________\n" << RESET;
                            cout << endl;
                            cout << RED << "[+] " << RESET << "SHA-256 Hash: " << RED << sha_hash << RESET << endl;
                            cout << BLUE << "_________________________________________________________________\n" << RESET;
                        }
                    
                        else if (action == "R" || action == "r") {
                            string inputHash;
                            cout << YELLOW << "[>] " << RESET << "Enter SHA-256 hash to reverse: ";
                            cin >> inputHash;
                    
                            string method;
                            cout << endl;
                            cout << BLUE << "_____________________ " << GREEN << "Reversing  Method" << RESET << BLUE <<  " _________________________\n" << RESET;
                            cout << endl;
                            cout << YELLOW << "[1]" << RESET << " Use online browser\n";
                            cout << YELLOW << "[2]" << RESET << " Use local wordlist\n";
                            cout << BLUE << "_________________________________________________________________\n" << RESET;
                            cout << endl;
                            cout << YELLOW << "[>] " << RESET << "Enter option: ";
                            cin >> method;
                            cout << endl;
                    
                            if (method == "1") {
                                cout << GREEN << "[-] " << RESET << "Opening your browser..." << endl;
                                openSHA256OnlineLookup(inputHash);
                            } 
                            
                            else if (method == "2") {
                                string wordlistPath = "wordlist.txt";
                                cout << ORANGE << "[?] " << RESET << "Searching local wordlist..." << endl;
                                string result = searchSHA256Wordlist(inputHash, wordlistPath);
                                cout << BLUE << "_________________________________________________________________\n" << RESET;
                                cout << endl;
                                cout << GREEN << "[-] " << RESET << "Result: " << GREEN << result << RESET << endl;
                                cout << BLUE << "_________________________________________________________________\n" << RESET;
                            } 
                            
                            else {
                                cout << RED << "[!] Invalid method choice." << RESET << endl;
                            }
                        }

                        else {
                                cout << endl;
                                cout << RED << "[x] " << RESET << "Invalid Option Selected" << endl;
                                cout << endl;
                        }
                    }
                    
                    else {
                        cout << endl;
                        cout << RED << "[x] " << RESET << "Invalid Option Selected" << endl;
                        cout << endl;
                    }
            }

            else if (hash_choice == "3" || hash_choice == "03" || hash_choice == "Hash Identifier" || hash_choice == "hash identifier") {
                        std::string hashInput;
                        cout << endl;
                        cout << YELLOW << "[>] " << RESET << "Enter hash to identify: ";
                        cin.ignore(); // Clear newline
                        getline(cin, hashInput);

                        cout << ORANGE << "[!] " << RESET << "Identifying the hash..." << endl;
                        std::string result = identifyHashLocally(hashInput);

                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                        cout << endl;
                        cout << GREEN << "[-]" << RESET << " Identified hash: " << GREEN << result << RESET << endl;
                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                     }

                     else if (hash_choice == "4" || hash_choice == "04" || hash_choice == "Hash Reversor" || hash_choice == "hash reversor") {
                        std::string hashing, hashingType;
                        std::cout << std::endl;

                        std::cout << YELLOW << "[>] " << RESET << "Enter hash to reverse: ";
                        std::cin.ignore(); // Clear newline
                        std::getline(std::cin, hashing);

                        std::cout << std::endl;
                        std::cout << BLUE << "_____________________ " << RESET << GREEN << "Supported Hash Types" << RESET << BLUE << " _____________________\n" << RESET;
                        std::cout << endl;
                        std::cout << YELLOW << "[1]" << RESET << " md5"     << YELLOW << "             [5]" << RESET <<  " sha1"     << YELLOW << "            [9]" << RESET <<  " mysql5" << endl;
                        std::cout << YELLOW << "[2]" << RESET << " sha256"  << YELLOW << "          [6]" << RESET <<  " sha384"   << YELLOW << "          [10]" << RESET <<  " ripemd160" << endl;
                        std::cout << YELLOW << "[3]" << RESET << " sha512"  << YELLOW << "          [7]" << RESET <<  " ntlm"     << YELLOW << "            [11]" << RESET <<  " whirlpool" << endl;
                        std::cout << YELLOW << "[4]" << RESET << " lm"      << YELLOW << "              [8]" << RESET <<  " mysql"    << endl;      
                        std::cout << BLUE << "_________________________________________________________________\n" << RESET;

                        std::cout << std::endl;
                        std::cout << YELLOW << "[>] " << RESET << "Enter hash type (e.g. md5): ";
                        std::getline(std::cin, hashingType);

                        std::cout << std::endl;
                        std::cout << ORANGE << "[!] " << RESET << "Querying API..." << std::endl;

                        std::string result = reverseHashAPI(hashing, hashingType);

                        std::cout << std::endl;
                        std::cout << BLUE << "_________________________________________________________________\n" << RESET;
                        std::cout << endl;
                        std::cout << GREEN << "[-]" << RESET << " Result: " << GREEN << result << RESET << std::endl;
                        std::cout << BLUE << "_________________________________________________________________\n" << RESET;
                     }

                     else {
                            cout << endl;
                            cout << RED << "[x] " << RESET << "Invalid Option Selected" << endl;
                            cout << endl;
                    }
        }

        else if (choice == "4" || choice == "04" || choice == "Other" || choice == "Other") {
            string sub_choice;
            cout << endl;
            cout << BLUE << "_____________________" << RESET<< GREEN << " Other Algorithms "<< RESET << BLUE << "__________________________" << RESET << endl;
            cout << endl;
            cout << YELLOW << "[1]" << RESET << " Letter <-> Number Converter" << endl;
            cout << YELLOW << "[2]" << RESET << " Modulus" << endl;
            cout << YELLOW << "[3]" << RESET << " Hexadecimal" << endl;
            cout << YELLOW << "[4]" << RESET << " Character Counter" << endl;
            cout << BLUE << "_________________________________________________________________\n" << RESET;
            cout << endl;
            cout << YELLOW << "[>] " << RESET<< "Select an algorithm: ";
            cin >> sub_choice;
            cout << endl;

            if (sub_choice == "1" || sub_choice == "01" || sub_choice == "Letter" || sub_choice == "Converter") {
                string convertOption;
                cout << endl;
                cout << BLUE << "___________________" << RESET<< GREEN << " Choose conversion type "<< RESET << BLUE << "______________________" << RESET << endl;
                cout << endl;
                cout << YELLOW << "[1]" << RESET << " Letters to Numbers" << endl;
                cout << YELLOW << "[2]" << RESET << " Numbers to Letters" << endl;
                cout << BLUE << "_________________________________________________________________\n" << RESET;

                cout << endl;

                cout << YELLOW << "[>] " << RESET<< "Enter 1 or 2: ";
                cin >> convertOption;
        
                cout << endl;
        
                if (convertOption == "1") {
                    // Ask the user for the shift mapping style
                    int mapping;
                    cout << endl;

                    cout << BLUE << "__________" << RESET<< GREEN << " Select the letter-to-number mapping style "<< RESET << BLUE << "____________" << RESET << endl;
                    cout << endl;
                    cout << YELLOW << "[1]" << RESET << " A=1, B=2, ..., Z=26" << endl;
                    cout << YELLOW << "[2]" << RESET << " A=0, B=1, ..., Z=25" << endl;
                    cout << BLUE << "_________________________________________________________________\n" << RESET;
                    cout << endl;
                    cout << YELLOW << "[>] " << RESET<< "Enter 1 or 2: ";
                    cin >> mapping;
                    cout << endl;


                    string input;
                    cout << YELLOW << "[>] " << RESET<< "Enter letters: ";
                    cin >> input;
        
                    vector<int> numbers = Converter::stringToNumbers(input, mapping);
                    cout << BLUE << "_________________________________________________________________\n" << RESET;
                    cout << endl;
                    cout << RED << "[+] " RESET << "Converted Numbers: ";

                    for (int num : numbers) {
                        cout << RED << num << RESET << " ";
                    }

                    cout << endl;
                    cout << BLUE << "_________________________________________________________________\n" << RESET;
                } 
                
                else if (convertOption == "2") {
                    // Ask the user for the shift mapping style
                    int mapping;
                    cout << endl;

                    cout << BLUE << "__________" << RESET<< GREEN << " Select the letter-to-number mapping style "<< RESET << BLUE << "____________" << RESET << endl;
                    cout << endl;
                    cout << YELLOW << "[1]" << RESET << " A=1, B=2, ..., Z=26" << endl;
                    cout << YELLOW << "[2]" << RESET << " A=0, B=1, ..., Z=25" << endl;
                    cout << BLUE << "_________________________________________________________________\n" << RESET;
                    cout << endl;
                    cout << YELLOW << "[>] " << RESET<< "Enter 1 or 2: ";
                    cin >> mapping;
                    cout << endl;

                    int count;
                    cout << YELLOW << "[>] " << RESET<< "How many numbers will you enter? ";
                    cin >> count;
                
                    vector<int> numbers;
                    cout << YELLOW << "[>] " << RESET<< "Enter " << count << " numbers (separated by space): ";

                    for (int i = 0; i < count; i++) {
                        int num;
                        cin >> num;
                        numbers.push_back(num);
                    }
        
                    string letters = Converter::numbersToString(numbers, mapping);
                    cout << BLUE << "_________________________________________________________________\n" << RESET;
                    cout << endl;
                    cout << RED << "[+] " RESET << "Converted Letters: " << RED << letters << RESET << endl;
                    cout << BLUE << "_________________________________________________________________\n" << RESET;
                }
            
                else {
                    cout << RED << "[x] " << RESET << "Invalid conversion option selected." << endl;
                    cout << endl;
                }
            }

            else if (sub_choice == "2" || sub_choice == "02" || sub_choice == "Modulus") {
                int a, b;

                cout << YELLOW << "[>] " << RESET<< "Enter two integers (a mod b): ";
                cin >> a >> b;
    
                try {
                    int result = modulus_operation(a, b);

                    cout << BLUE << "_________________________________________________________________\n" << RESET;
                    cout << endl;
                    cout << CYAN << "[#] " RESET << "Result of " << a << " mod " << b << " = " << CYAN << result << RESET << endl;
                    cout << BLUE << "_________________________________________________________________\n" << RESET;
                } 
                
                catch (const exception& e) {
                    cout << RED << "[x] " << RESET << "Error: " << e.what() << endl;
                    cout << endl;
                    displayLogo2();
                    cout << endl;
                }
            }

            else if (sub_choice == "3" || sub_choice == "03" || sub_choice == "Other" || sub_choice == "Hexadecimal") { 
                string hex_choice;

                cout << endl;
                cout << BLUE << "___________________" << RESET<< GREEN << " Hexadecimal Algorithms "<< RESET << BLUE << "______________________" << RESET << endl;
                cout << endl;
                cout << YELLOW << "[1]" << RESET << " Checksum" << endl;
                cout << YELLOW << "[2]" << RESET << " Conversion" << endl;
                cout << BLUE << "_________________________________________________________________\n" << RESET;
                cout << endl;

                cout << YELLOW << "[>] " << RESET<< "Select an algorithm: ";
                cin >> hex_choice;

                if (hex_choice == "1" || hex_choice == "01" || hex_choice == "checksum") {
                    int blockCount;

                    cout << endl;
                    cout << YELLOW << "[>] " << RESET<< "Enter the number of hexadecimal blocks you want to input: ";
                    cin >> blockCount;
                    cin.ignore(); // clear newline from buffer
        
                    vector<vector<string>> hexBlocks;

                    for (int i = 0; i < blockCount; ++i) {
                        cout << YELLOW << "[>] " << RESET<< "Enter space-separated hexadecimal values for block " << i + 1 << ": ";
                        string line;
                        getline(cin, line);
                        stringstream ss(line);
                        vector<string> block;
                        string hexVal;

                        while (ss >> hexVal) {
                            block.push_back(hexVal);
                        }

                        hexBlocks.push_back(block);
                    }
        
                    vector<string> checksum = Hexadecimal::calculateChecksum(hexBlocks);

                    cout << BLUE << "_________________________________________________________________\n" << RESET;
                    cout << endl;
                    cout << RED << "[+] " RESET << "Checksum: ";

                    for (const auto& hex : checksum) {
                        cout << RED << hex << RESET << " ";
                    }

                    cout << endl;
                    cout << BLUE << "_________________________________________________________________\n" << RESET;
                }  
        
                else if (hex_choice == "2" || hex_choice == "02" || hex_choice == "conversion") {
                    string conv_choice;
                    cout << endl;
                    cout << BLUE << "_____________________" << RESET<< GREEN << " Types of Conversion "<< RESET << BLUE << "_______________________" << RESET << endl;
                    cout << endl;
                    cout << YELLOW << "[1]" << RESET << " Text to Hexadecimal" << endl;
                    cout << YELLOW << "[2]" << RESET << " Hexadecimal to Text" << endl;
                    cout << BLUE << "_________________________________________________________________\n" << RESET;
                    cout << endl;
                    cout << YELLOW << "[>] " << RESET<< "Choose conversion type: ";
                    cin >> conv_choice;
                    cin.ignore();
        
                    if (conv_choice == "1" || conv_choice == "01" || conv_choice == "text") {
                        string inputText;
                        cout << endl;
                        cout << YELLOW << "[>] " << RESET<< "Enter text to convert to hexadecimal: ";
                        getline(cin, inputText);
                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                        cout << endl;
                        cout << RED << "[+] " RESET << "Hexadecimal: " << RED << HexConversion::textToHex(inputText) << RESET << endl;
                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                    }

                    else if (conv_choice == "2" || conv_choice == "02" || conv_choice == "hex") {
                        string hexLine;
                        cout << endl;

                        cout << YELLOW << "[>] " << RESET<< "Enter space-separated hexadecimal values: ";
                        getline(cin, hexLine);

                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                        cout << endl;
                        cout << GREEN << "[-] " << RESET << "Text: " << GREEN << HexConversion::hexToText(hexLine) << RESET << endl;
                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                    }

                    else {
                        cout << endl;
                        cout << RED << "[x] " << RESET << "Invalid conversion type. Please select 1 or 2." << endl;
                        cout << endl;
                    }
                }        

                else {
                        cout << endl;
                        cout << RED << "[x] " << RESET << "Invalid sub-choice. Please select a valid option." << endl;
                        cout << endl;
                }
            }

            else if (sub_choice == "4" || sub_choice == "04" || sub_choice == "Character" || sub_choice == "Counter") {
                string text;
                cin.ignore(); // clear buffer
                cout << YELLOW << "[>] " << RESET<< "Enter text: ";
                getline(cin, text);
            
                int count = CharacterCounter::countCharacters(text);
            
                cout << BLUE << "_________________________________________________________________\n" << RESET;
                cout << endl;
                cout << RED << "[+] " RESET << "Total Characters (including spaces): " << RED << count << RESET << endl;
                cout << BLUE << "_________________________________________________________________\n" << RESET;
            }            

            else {
                cout << endl;
                cout << RED << "[x] " << RESET << "Invalid Option Selected" << endl;
                cout << endl;
            }
        }

        else if (choice == "5" || choice == "05" || choice == "Advanced" || choice == "advanced"){
            cout << endl;
            cout << RED<< "[!]" << RESET << " Currently not available" << endl;
        }

        else if (choice == "6" || choice == "06" || choice == "CTF" || choice == "ctf") {
            string sub_choice;
            cout << endl;

            cout << BLUE << "________________________" << RESET<< GREEN << " CTF Algorithms "<< RESET << BLUE << "_________________________" << RESET << endl;
            cout << endl;
            cout << YELLOW << "[1]" << RESET << " RSA                              " << RESET << YELLOW << "[5]" << RESET << " Base64 Decoder" << endl;
            cout << YELLOW << "[2]" << RESET << " FactorDB                         " << RESET << YELLOW << "[6]" << RESET << " ROT13" << endl;
            cout << YELLOW << "[3]" << RESET << " Substitution Cipher              " << RESET << YELLOW << "[7]" << RESET << " Convertion" << endl;
            cout << YELLOW << "[4]" << RESET << " Morse Code                       " << RESET << YELLOW << "[8]" << RESET << " Framework" << endl;
            cout << BLUE << "_________________________________________________________________\n" << RESET;
            cout << endl;
            cout << YELLOW << "[>] " << RESET<< "Select an algorithm: ";
            std::cin >> sub_choice;
            std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');  // Clear input buffer
            std::cout << std::endl;

            if (sub_choice == "1" || sub_choice == "01" || sub_choice == "RSA" || sub_choice == "rsa") {
                    string rsa_choice;

                    cout << BLUE << "_________________________" << RESET<< GREEN << " RSA Options "<< RESET << BLUE << "___________________________" << RESET << endl;
                    cout << endl;
                    cout << YELLOW << "[01]" << RESET << GREEN << " Standard RSA     " << RESET << "Decrypt c using e, p & q" << endl;
                    cout << YELLOW << "[02]" << RESET << GREEN << " Non co-prime     " << RESET << "Decrypt c using e, p & q" << endl;
                    cout << YELLOW << "[03]" << RESET << GREEN << " Exposed Keys     " << RESET << "Decrypt c using e, n & dp" << endl;
                    cout << YELLOW << "[04]" << RESET << GREEN << " RSA CRT leak     " << RESET << "Decrypt c using e, n, dp & dq" << endl;
                    cout << YELLOW << "[05]" << RESET << GREEN << " Generic RSA      " << RESET << "Decrypt c using e & n" << endl;
                    cout << YELLOW << "[06]" << RESET << GREEN << " Factoring-based  " << RESET << "Decrypt c using e & n (recommended)" << endl;
                    cout << YELLOW << "[07]" << RESET << GREEN << " Partial key      " << RESET << "Decrypt c using e & 1 n exponent (p)" << endl;
                    cout << YELLOW << "[08]" << RESET << GREEN << " Incorrect setup  " << RESET << "Decrypt c where n is prime" << endl;
                    cout << YELLOW << "[09]" << RESET << GREEN << " Low e attack     " << RESET << "Decrypt c where e is smaller" << endl;
                    cout << YELLOW << "[10]" << RESET << GREEN << " Cubic attack     " << RESET << "Decrypt c where e = 3" << endl;
                    cout << YELLOW << "[11]" << RESET << GREEN << " Common modulus   " << RESET << "Decrypt c where n is identical using e1 & e2" << endl;
                    cout << YELLOW << "[12]" << RESET << GREEN << " Wieners attack   " << RESET << "Decrypt c with n where e is larger" << endl;
                    cout << YELLOW << "[13]" << RESET << GREEN << " RSA Oracle Trick " << RESET << "Decrypt c with n & e" << endl;
                    cout << YELLOW << "[14]" << RESET << GREEN << " RSA Cert Decoder " << RESET << "Analyze the RSA Certificate" << endl;
                    cout << YELLOW << "[15]" << RESET << GREEN << " Tripple n RSA    " << RESET << "Decrypt c with n1, n2, n3 & e" << endl;
                    cout << YELLOW << "[16]" << RESET << GREEN << " (M ** e) attack  " << RESET << "Decrypt c with n & e" << endl;
                    cout << YELLOW << "[17]" << RESET << GREEN << " Hastad Broadcast " << RESET << "Decrypt c1, c2 & c3 with n1, n2, n3 & e" << endl;
                    cout << YELLOW << "[18]" << RESET << GREEN << " Pollard's p - 1  " << RESET << "Decrypt c with n" << endl;
                    cout << YELLOW << "[19]" << RESET << GREEN << " Pollard's attack " << RESET << "Decrypt c with n, e & x" << endl;
                    cout << YELLOW << "[20]" << RESET << GREEN << " Key generation   " << RESET << "Calculate RSA values p,q,n,e,d & phi (m)" << endl;
                    cout << BLUE << "_________________________________________________________________\n" << RESET;
                    cout << endl;
                    cout << YELLOW << "[>] " << RESET<< "Select an option: ";
                    cin >> rsa_choice;
                    std::cin.ignore();
                    cout << endl;
                
                    if (rsa_choice == "1" || rsa_choice == "01") {
                            std::string e, p, q, c;

                            std::cout << YELLOW << "[>] " << RESET << "Enter public exponent (e): ";
                            std::cin >> e;
                            std::cout << YELLOW << "[>] " << RESET << "Enter prime p: ";
                            std::cin >> p;
                            std::cout << YELLOW << "[>] " << RESET << "Enter prime q: ";
                            std::cin >> q;
                            std::cout << YELLOW << "[>] " << RESET << "Enter ciphertext (c): ";
                            std::cin >> c;

                            std::string decrypted = decryptRSA(c, e, p, q);

                            cout << BLUE << "_________________________________________________________________\n" << RESET;
                            cout << endl;
                            std::cout << GREEN << "[-] " << RESET << "Decrypted plaintext: " << GREEN << decrypted << RESET << std::endl;
                            cout << BLUE << "_________________________________________________________________\n" << RESET;
                        }

                        else if (rsa_choice == "02" || rsa_choice == "2"){
                            
                        }
                        
                        else if (rsa_choice == "3" || rsa_choice == "03") {
                            mpz_class e, n, dp, c;

                            std::cout << YELLOW << "[>]" << RESET << " Enter e: ";
                            std::cin >> e;

                            std::cout << YELLOW << "[>]" << RESET << " Enter n: ";
                            std::cin >> n;

                            std::cout << YELLOW << "[>]" << RESET << " Enter dp: ";
                            std::cin >> dp;

                            std::cout << YELLOW << "[>]" << RESET << " Enter c (ciphertext): ";
                            std::cin >> c;

                            mpz_class m = reconstruct_private_key_and_decrypt(e, n, dp, c);

                            std::stringstream ss;
                            ss << std::hex << m;
                            std::string hexStr = ss.str();

                            // Remove leading '0x' and odd length if needed
                            if (hexStr.length() % 2 != 0)
                                    hexStr = "0" + hexStr;

                                    std::string message = hex_to_ascii(hexStr);
                                    cout << BLUE << "_________________________________________________________________\n" << RESET;
                                    cout << endl;
                                    std::cout << GREEN << "[-]" << RESET << " Decrypted message: " << GREEN << message << RESET << std::endl;
                                    cout << BLUE << "_________________________________________________________________\n" << RESET;
                        }

                        else if (rsa_choice == "4" || rsa_choice == "04"){
                              mpz_class c, p, q, dp, dq;

                                std::cout << YELLOW << "[>]" << RESET << " Enter ciphertext (c): ";
                                std::cin >> c;
                                std::cout << YELLOW << "[>]" << RESET << " Enter prime p: ";
                                std::cin >> p;
                                std::cout << YELLOW << "[>]" << RESET << " Enter prime q: ";
                                std::cin >> q;
                                std::cout << YELLOW << "[>]" << RESET << " Enter dp (d mod p-1): ";
                                std::cin >> dp;
                                std::cout << YELLOW << "[>]" << RESET << " Enter dq (d mod q-1): ";
                                std::cin >> dq;

                                mpz_class m = decrypt_with_dp_dq(c, p, q, dp, dq);

                                // Convert to hex
                                std::stringstream ss;
                                ss << std::hex << m;
                                std::string hexStr = ss.str();

                                // Ensure even length for hex string
                                if (hexStr.length() % 2 != 0)
                                        hexStr = "0" + hexStr;

                                std::string plaintext = hex_to_ascii_crt(hexStr);
                                
                                cout << BLUE << "_________________________________________________________________\n" << RESET;
                                cout << endl;
                                std::cout << GREEN << "[-]" << RESET << " Decrypted message: " << GREEN << plaintext << RESET << std::endl; 
                                cout << BLUE << "_________________________________________________________________\n" << RESET;
                        }

                        else if (rsa_choice == "5" || rsa_choice == "05") {
                                std::string e, n, c;
                                std::cout << YELLOW << "[>] " << RESET << "Enter public exponent (e): ";
                                std::cin >> e;
                                std::cout << YELLOW << "[>] " << RESET << "Enter modulus (n): ";
                                std::cin >> n;
                                std::cout << YELLOW << "[>] " << RESET << "Enter ciphertext (c): ";
                                std::cin >> c;

                                std::string decrypted = decryptRSAWithNandE(c, e, n);

                                std::cout << BLUE << "_________________________________________________________________\n" << RESET;
                                std::cout << endl;
                                std::cout << GREEN << "[-]" << RESET << " Decrypted plaintext: " << GREEN << decrypted << RESET << std::endl;
                                std::cout << BLUE << "_________________________________________________________________\n" << RESET;
                            }

                            else if (rsa_choice == "6" || rsa_choice == "06"){
                                    solve_srsa();
                            }

                            else if (rsa_choice == "7" || rsa_choice == "07") {
                                    std::string c, e, p;

                                    std::cout << YELLOW << "[>]" << RESET << " Enter public exponent (e): ";
                                    std::getline(std::cin, e);

                                    std::cout << YELLOW << "[>]" << RESET << " Enter factorized n value (p): ";
                                    std::getline(std::cin, p);

                                    std::cout << YELLOW << "[>]" << RESET << " Enter ciphertext (c): ";
                                    std::getline(std::cin, c);

                                    std::string plaintext = decryptRSASquareN(c, e, p);

                                    std::cout << BLUE << "_________________________________________________________________\n" << RESET;
                                    std::cout << endl;
                                    std::cout << GREEN << "[-]" << RESET << " Decrypted plaintext: " << GREEN << plaintext << RESET << endl;
                                    std::cout << BLUE << "_________________________________________________________________\n" << RESET;
                            }

                            else if (rsa_choice == "8" || rsa_choice == "08") {
                                std::string n_str, c_str;
                                unsigned long e;

                                std::cout << YELLOW << "[>]" << RESET << "Enter the prime n: ";
                                std::cin >> n_str;
                                std::cout << YELLOW << "[>]" << RESET << "Enter ciphertext c: ";
                                std::cin >> c_str;
                                std::cout << YELLOW << "[>]" << RESET << "Enter public exponent e: ";
                                std::cin >> e;

                                RSADecryptor decryptor(n_str, c_str, e);
                                std::string plaintext = decryptor.decrypt();
                                
                                std::cout << BLUE << "_________________________________________________________________\n" << RESET;
                                std::cout << endl;
                                std::cout << GREEN << "[-]" << RESET << " Decrypted message: " << GREEN << plaintext << RESET << std::endl;
                                std::cout << BLUE << "_________________________________________________________________\n" << RESET;
                            }

                            else if (rsa_choice == "9" || rsa_choice == "09") {
                                mpz_class n, e, c;

                                std::cout << YELLOW << "[>]" << RESET << " Enter modulus (n): " << RESET;
                                std::cin >> n;
                                std::cout << YELLOW << "[>]" << RESET << " Enter public exponent (e): " << RESET;
                                std::cin >> e;
                                std::cout << YELLOW << "[>]" << RESET << " Enter ciphertext (c): " << RESET;
                                std::cin >> c;

                                RSALowExpDecryptor decryptor(n, e, c);
                                std::string message = decryptor.decryptToAscii();

                                std::cout << BLUE << "_________________________________________________________________\n" << RESET;
                                std::cout << endl;
                                std::cout << GREEN << "[-]" << RESET << " Decrypted message (ASCII): " << GREEN << message << RESET << std::endl;
                                std::cout << BLUE << "_________________________________________________________________\n" << RESET;
                            }

                            else if (rsa_choice == "10") {
                               std::string str_e, str_n, str_c;
                                std::cout << YELLOW << "[>]" << RESET << " Enter e: ";
                                std::cin >> str_e;
                                std::cout << YELLOW << "[>]" << RESET << " Enter n: ";
                                std::cin >> str_n;
                                std::cout << YELLOW << "[>]" << RESET << " Enter ciphertext c: ";
                                std::cin >> str_c;

                                mpz_class e(str_e), n(str_n), c(str_c);

                                RSACubeRootDecryptor decryptor(e, n, c);
                                std::cout << RED << "[!]" << RESET << " Attempting cube root decryption...\n";
                                mpz_class m = decryptor.decrypt();

                                std::cout << BLUE << "_________________________________________________________________\n" << RESET;
                                std::cout << endl;
                                std::cout << GREEN << "[-]" << RESET << " Decrypted Integer (m): " << GREEN << m << RESET << endl;
                                std::cout << BLUE << "_________________________________________________________________\n" << RESET;
                                std::string ascii = decryptor.decryptToAscii();
                                std::cout << BLUE << "_________________________________________________________________\n" << RESET;
                                std:: cout << endl;
                                std::cout << GREEN << "[-]" << RESET << " Decrypted ASCII: " << GREEN << ascii << RESET << endl;
                                std::cout << BLUE << "_________________________________________________________________\n" << RESET;
                            }

                            else if (rsa_choice == "11"){
                                std::string n_str, e1_str, e2_str, c_str;

                                std::cout << YELLOW << "[>]" << RESET << " Enter n (decimal): ";
                                std::getline(std::cin, n_str);
                                std::cout << YELLOW << "[>]" << RESET << " Enter e1 (decimal): ";
                                std::getline(std::cin, e1_str);
                                std::cout << YELLOW << "[>]" << RESET << " Enter e2 (decimal): ";
                                std::getline(std::cin, e2_str);
                                std::cout << YELLOW << "[>]" << RESET << " Enter ciphertext c (decimal): ";
                                std::getline(std::cin, c_str);

                                mpz_class n(n_str), e1(e1_str), e2(e2_str), c(c_str);

                                std::string decrypted = wiener_attack_decrypt(n, e1, e2, c);

                                if (!decrypted.empty()) {
                                        std::cout << BLUE << "_________________________________________________________________\n" << RESET;
                                        std::cout << endl;
                                        std::cout << GREEN << "[-]" << RESET << " Decrypted message: " << GREEN << decrypted << RESET << std::endl;
                                        std::cout << BLUE << "_________________________________________________________________\n" << RESET;
                                } else {
                                            std::cout << BLUE << "_________________________________________________________________\n" << RESET;
                                            std::cout << endl;
                                            std::cout << RED << "[!]" << RESET << " No message could be decrypted.\n";
                                            std::cout << BLUE << "_________________________________________________________________\n" << RESET;
                                    }
                            }

                            else if (rsa_choice == "12"){
                                std::string e_str, n_str, c_str;
                                std::cout << YELLOW << "[>]" << RESET << " Enter public exponent (e): ";
                                std::getline(std::cin, e_str);
                                std::cout << YELLOW << "[>]" << RESET << " Enter modulus (n): ";
                                std::getline(std::cin, n_str);
                                std::cout << YELLOW << "[>]" << RESET << " Enter ciphertext (c): ";
                                std::getline(std::cin, c_str);

                                mpz_class e(e_str);
                                mpz_class n(n_str);
                                mpz_class c(c_str);

                                mpz_class d = wienerAttack(e, n);

                                if (d == mpz_class(0)) {
                                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                                        cout << endl;
                                        std::cout << RED << "[!]" << RESET << " Attack failed. Private key not recovered.\n";
                                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                                } else {
                                            cout << BLUE << "_________________________________________________________________\n" << RESET;
                                            cout << endl;
                                            std::cout << GREEN << "[-]" << RESET << " Private exponent (d) found: " << GREEN << d << RESET << endl;
                                            cout << BLUE << "_________________________________________________________________\n" << RESET;
                                            std::string plaintext = decryptRSA(c, d, n);
                                            cout << BLUE << "_________________________________________________________________\n" << RESET;
                                            cout << endl;
                                            std::cout << GREEN << "[-]" << RESET << " Decrypted message: " << GREEN << plaintext << RESET << endl;
                                            cout << BLUE << "_________________________________________________________________\n" << RESET;
                                }
                            }

                            else if (rsa_choice == "13"){
                                string n_str, e_str, c_str, m_prime_str;

                                cout << YELLOW << "[>]" << RESET << " Enter n: ";
                                getline(cin, n_str);
                                cout << YELLOW << "[>]" << RESET << " Enter e: ";
                                getline(cin, e_str);
                                cout << YELLOW << "[>]" << RESET << " Enter c (flag ciphertext): ";
                                getline(cin, c_str);

                                Integer n(n_str.c_str());
                                Integer e(e_str.c_str());
                                Integer c(c_str.c_str());

                                RSAOracle oracle(n, e);

                                Integer modified_c = oracle.getModifiedCiphertext(c);
                                cout << BLUE << "_________________________________________________________________\n" << RESET;
                                cout << endl;
                                cout << RED << "[+]" << RESET << " Modified ciphertext to send to oracle: " << RED << modified_c << RESET << endl;
                                cout << BLUE << "_________________________________________________________________\n" << RESET;
                                cout << endl;

                                cout << YELLOW << "[>]" << RESET << " Enter oracle decrypted value (m_prime): ";
                                getline(cin, m_prime_str);
                                Integer m_prime(m_prime_str.c_str());

                                Integer m = oracle.recoverMessage(m_prime);
                                string flag = RSAOracle::integerToString(m);
                                
                                cout << BLUE << "_________________________________________________________________\n" << RESET;
                                cout << endl;
                                cout << GREEN << "[-]" << RESET << " Decrypted flag: " << GREEN <<  flag << RESET << endl;
                                cout << BLUE << "_________________________________________________________________\n" << RESET;
                            }

                            else if (rsa_choice == "14"){
                                std::string pemCert;
                                std::cout << YELLOW << "[>]" << RESET << " Enter PEM certificate (end input with a single line containing only 'END'): ";
    
                                std::string line;
                                while (std::getline(std::cin, line)) {
                                            if (line == "END") break;
                                                    pemCert += line + "\n";
                                }
    
                                RSADecoder decoder;
                                decoder.decodeCertificate(pemCert);
                            }

                            else if (rsa_choice == "15"){
                                solveTripleRSA();
                            }
                            
                            else if (rsa_choice == "16"){
                                std::string N, e, c;

                                std::cout << YELLOW <<  "[>]" << RESET << " Enter N (modulus): ";
                                std::getline(std::cin, N);

                                std::cout << YELLOW <<  "[>]" << RESET << " Enter e (exponent): ";
                                std::getline(std::cin, e);

                                std::cout << YELLOW <<  "[>]" << RESET << " Enter c (ciphertext): ";
                                std::getline(std::cin, c);

                                MiniRSA rsa(N, e, c);
                                std::string flag = rsa.decrypt();
                                
                                cout << BLUE << "_________________________________________________________________\n" << RESET;
                                cout << endl;
                                cout << GREEN << "[-]" << RESET << " Decrypted flag: " << GREEN << flag << RESET << endl;
                                cout << BLUE << "_________________________________________________________________\n" << RESET;
                            }

                            else if (rsa_choice == "17"){
                                std::vector<mpz_class> c(3), n(3);
                                unsigned int e;

                                std::cout << YELLOW << "[>]" << RESET << " Enter public exponent e (e.g., 3): ";
                                std::cin >> e;

                                // Clear the newline from buffer after reading e
                                std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');

                                for (int i = 0; i < 3; ++i) {
                                        std::string n_str, c_str;
                                        std::cout << std::endl;
                                        std::cout << GREEN << "    Friend " << i + 1 << RESET << endl;
                                        std::cout << YELLOW << "[>]" << RESET << " Enter n" << i + 1 << ": ";
                                        std::getline(std::cin, n_str);
                                        std::cout << YELLOW << "[>]" << RESET << " Enter c" << i + 1 << ": ";
                                        std::getline(std::cin, c_str);

                                        n[i].set_str(n_str, 10);
                                        c[i].set_str(c_str, 10);
                                    }

                                    std::string decrypted = decrypt_message(c, n, e);
                                    cout << BLUE << "_________________________________________________________________\n" << RESET;
                                    cout << endl;
                                    std::cout << GREEN << "[-]" << RESET << " Decrypted message: " << GREEN << decrypted << RESET << std::endl;
                                    cout << BLUE << "_________________________________________________________________\n" << RESET;
                            }

                            else if (rsa_choice == "18"){
                                    std::string hex_n, hex_c;

                                    std::cout << YELLOW << "[>]" << RESET << " Enter modulus n (hex): ";
                                    std::getline(std::cin, hex_n);

                                    std::cout << YELLOW << "[>]" << RESET << " Enter ciphertext c (hex): ";
                                    std::getline(std::cin, hex_c);

                                    PollardSolver solver(hex_n, hex_c);

                                    if (solver.factorize()) {
                                        std::string flag = solver.getFlag();
                                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                                        cout << endl;
                                        std::cout << GREEN << "[-]" << RESET << " Decrypted flag: " << GREEN << flag << RESET << std::endl;
                                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                                    } else {
                                                cout << BLUE << "_________________________________________________________________\n" << RESET;
                                                cout << endl;
                                                std::cerr << RED << "[x]" << RESET << " Factorization failed!" << std::endl;
                                                cout << BLUE << "_________________________________________________________________\n" << RESET;
                                    }
                            }

                            else if (rsa_choice == "19"){
                                std::string x_str, n_str, c_str, e_str;

                                std::cout << YELLOW << "[>]" << RESET << " Enter x (hex or decimal): ";
                                std::getline(std::cin, x_str);

                                std::cout << YELLOW << "[>]" << RESET << " Enter n (hex or decimal): ";
                                std::getline(std::cin, n_str);

                                std::cout << YELLOW << "[>]" << RESET << " Enter c (hex or decimal): ";
                                std::getline(std::cin, c_str);

                                std::cout << YELLOW << "[>]" << RESET << " Enter e (decimal): ";
                                std::getline(std::cin, e_str);

                                // Minimal inline hex-fix (no helper function used)
                                if (!x_str.empty() && x_str.find("0x") != 0 && x_str.find_first_of("abcdefABCDEF") != std::string::npos)
                                        x_str = "0x" + x_str;
                                if (!n_str.empty() && n_str.find("0x") != 0 && n_str.find_first_of("abcdefABCDEF") != std::string::npos)
                                        n_str = "0x" + n_str;
                                if (!c_str.empty() && c_str.find("0x") != 0 && c_str.find_first_of("abcdefABCDEF") != std::string::npos)
                                        c_str = "0x" + c_str;

                                try {
                                        mpz_class x(x_str, 0);
                                        mpz_class n(n_str, 0);
                                        mpz_class c(c_str, 0);
                                        mpz_class e(e_str, 10);

                                        PollardSolve solver(x, n, c, e);
                                        std::string flag = solver.decryptFlag();

                                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                                        cout << endl;
                                        std::cout << GREEN << "[-]" << RESET << " Decrypted Flag: " << GREEN << flag << RESET << std::endl;
                                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                                    } catch (const std::exception& ex) {
                                                cout << BLUE << "_________________________________________________________________\n" << RESET;
                                                cout << endl;
                                                std::cerr << RED << "[!]" << RESET << " Exception occurred: " << RED << ex.what() << RESET << std::endl;
                                                cout << BLUE << "_________________________________________________________________\n" << RESET;
                                    } catch (...) {     
                                                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                                                        cout << endl;
                                                        std::cerr << RED << "[!]" << RESET << " Unknown error occurred." << std::endl;
                                                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                                    }
                            }

                            else if (rsa_choice == "20") {
                                        RSASolver solver;
                                        int choice;
                                        mpz_class val1, val2;
                                        std::string temp;

                                        std::cout << BLUE << "____________________" << RESET << GREEN << " RSA Calculation Options " << RESET << BLUE << "____________________" << RESET << std::endl;
                                        std::cout << std::endl;
                                        std::cout << YELLOW << "[1]" << RESET << " Input p and q\n";
                                        std::cout << YELLOW << "[2]" << RESET << " Input p and n\n";
                                        std::cout << YELLOW << "[3]" << RESET << " Input q and n\n";
                                        std::cout << YELLOW << "[4]" << RESET << " Input n only (partial solve)\n";
                                        std::cout << BLUE << "_________________________________________________________________\n" << RESET;
                                        std::cout << std::endl;
                                        std::cout << YELLOW << "[>]" << RESET << " Choose input option: ";
                                        std::cin >> choice;
                                        std::cout << std::endl;

                                        switch (choice) {
                                            case 1:
                                                std::cout << YELLOW << "[>]" << RESET << " Enter p: "; std::cin >> temp; val1.set_str(temp, 10);
                                                std::cout << YELLOW << "[>]" << RESET << " Enter q: "; std::cin >> temp; val2.set_str(temp, 10);
                                                solver.inputPQ(val1, val2);
                                                break;
                                            case 2:
                                                std::cout << YELLOW << "[>]" << RESET << " Enter p: "; std::cin >> temp; val1.set_str(temp, 10);
                                                std::cout << YELLOW << "[>]" << RESET << " Enter n: "; std::cin >> temp; val2.set_str(temp, 10);
                                                solver.inputPN(val1, val2);
                                                break;
                                            case 3:
                                                std::cout << YELLOW << "[>]" << RESET << " Enter q: "; std::cin >> temp; val1.set_str(temp, 10);
                                                std::cout << YELLOW << "[>]" << RESET << " Enter n: "; std::cin >> temp; val2.set_str(temp, 10);
                                                solver.inputQN(val1, val2);
                                                break;
                                            case 4:
                                                std::cout << YELLOW << "[>]" << RESET << " Enter n: "; std::cin >> temp; val1.set_str(temp, 10);
                                                solver.inputN(val1);
                                                break;
                                            default:
                                                std::cout << BLUE << "_________________________________________________________________\n" << RESET;
                                                std::cout << std::endl;
                                                std::cout << RED << "[!]" << RESET << " Invalid choice.\n";
                                                std::cout << BLUE << "_________________________________________________________________\n" << RESET;
                                                break;
                                        }

                                        solver.solve();

                                        std::cout << BLUE << "_________________________________________________________________\n" << RESET;
                                        std::cout << std::endl;
                                        if (solver.getP() != 0)
                                                std::cout << GREEN << "[-]" << RESET << " p    = " << GREEN << solver.getP() << RESET << std::endl;

                                        if (solver.getQ() != 0)
                                                std::cout << GREEN << "[-]" << RESET << " q    = " << GREEN << solver.getQ() << RESET << std::endl;

                                        if (solver.getN() != 0)
                                                std::cout << GREEN << "[-]" << RESET << " n    = " << GREEN << solver.getN() << RESET << std::endl;

                                        if (solver.getPhi() != 0)
                                                std::cout << GREEN << "[-]" << RESET << " phi  = " << GREEN << solver.getPhi() << RESET << std::endl;

                                        if (solver.getE() != 0)
                                                std::cout << GREEN << "[-]" << RESET << " e    = " << GREEN << solver.getE() << RESET << std::endl;

                                        if (solver.getD() != 0)
                                                std::cout << GREEN << "[-]" << RESET << " d    = " << GREEN << solver.getD() << RESET << std::endl;
                                                std::cout << BLUE << "_________________________________________________________________\n" << RESET;

                                         // ✅ Only display this warning if p and q are actually missing
                                        if (solver.getP() == 0 && solver.getQ() == 0) {
                                                std::cout << BLUE << "_________________________________________________________________\n" << RESET;
                                                std::cout << std::endl;
                                                std::cout << RED << "[!]" << RESET << " Could not compute p or q. Are they missing or factoring required?\n";
                                                std::cout << BLUE << "_________________________________________________________________\n" << RESET;
                                            }

                                            std::cout << "\nPress Enter to continue...";
                                            std::cin.ignore();
                                            std::cin.get();
                                        }

                                        else {
                                                cout << endl;
                                                cout << RED << "[x] " << RESET << "Invalid Option Selected" << endl;
                                                cout << endl;
                                        }

            }                

            else if (sub_choice == "2" || sub_choice == "02" || sub_choice == "FactorDB" || sub_choice == "factordb") {
                        std::string n;

                        cout << YELLOW << "[>] " << RESET << "Enter modulus (n): ";
                        getline(cin >> std::ws, n);  // Skip leading whitespace safely

                        cout << BLUE << "\n[+] Querying FactorDB...\n" << RESET;
                        queryFactorDB(n);
            }


            else if (sub_choice == "3" || sub_choice == "03" || sub_choice == "Substitution" || sub_choice == "substitution") {
                cout << BLUE << "_________________" << RESET<< GREEN << " Substitution Cipher Options "<< RESET << BLUE << "___________________" << RESET << endl;
                cout << endl;
                std::cout << YELLOW << "[1]" << RESET << " Encrypt with known key\n";
                std::cout << YELLOW << "[2]" << RESET << " Decrypt with known key\n";
                std::cout << YELLOW << "[3]" << RESET << " Decrypt using frequency analysis (unknown key)\n";
                cout << BLUE << "_________________________________________________________________\n" << RESET;
                cout << endl;
                std::cout << YELLOW << "[>] " RESET << "Choose an option: ";

                SubstitutionCipher cipher;
                std::string input, key;
                int choice;

                
                std::cin >> choice;
                std::cin.ignore(); // clear newline
            
                switch (choice) {
                    case 1: {
                        cout << endl;
                        std::cout << YELLOW << "[>] " RESET << "Enter plaintext: ";
                        std::getline(std::cin, input);
            
                        std::cout << YELLOW << "[>] " << RESET << "Enter 26-letter substitution key (e.g., QWERTYUIOPASDFGHJKLZXCVBNM): ";
                        std::getline(std::cin, key);
            
                        if (key.size() != 26) {
                            std::cout << RED << "[!]" << RESET << " Key must be exactly 26 characters.\n";
                            break;
                        }
            
                        cipher.setKey(key);
                        std::string encrypted = cipher.encrypt(input);
                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                        cout << endl;
                        std::cout << RED << "[+]" << RESET << " Encrypted: " << encrypted << "\n";
                        cout << BLUE << "_________________________________________________________________\n" << RESET;
                        break;
                    }

                    case 2: {
                        cout << endl;
                        std::cout << YELLOW << "[>] " << RESET << "Enter ciphertext: ";
                        std::getline(std::cin, input);
            
                        std::cout << YELLOW << "[>]" << RESET << " Enter 26-letter substitution key: ";
                        std::getline(std::cin, key);
            
                        if (key.size() != 26) {
                            std::cout << RED << "[!]" << RESET << " Key must be exactly 26 characters.\n";
                            break;
                        }
            
                        cipher.setKey(key);
                            std::string decrypted = cipher.decrypt(input);
                            cout << BLUE << "_________________________________________________________________\n" << RESET;
                            cout << endl;
                            std::cout << GREEN << "[-]" << RESET << " Decrypted: " << GREEN <<  decrypted << RESET << "\n";
                            cout << BLUE << "_________________________________________________________________\n" << RESET;
                            break;
                        }

                        case 3: {
                                    SubstitutionSolver::openSolverInBrowser();
                                    break;
                        }

                        default:
                            std::cout << RED << "[!]" << RESET << " Invalid option.\n";
                    }
            }

            else if (sub_choice == "4" || sub_choice == "04" || sub_choice == "morse" || sub_choice == "Morse") {
                std::string input;
                cout << endl;
                std::cout << YELLOW << "[>]" << RESET << " Enter Morse code (use '/' for spaces between words): ";
                std::getline(std::cin, input);

                std::string decoded = MorseDecoder::decode(input);
                cout << BLUE << "_________________________________________________________________\n" << RESET;
                cout << endl;
                std::cout << GREEN << "[-]" << RESET << " Decoded text: " << GREEN << decoded << RESET << endl;
                cout << BLUE << "_________________________________________________________________\n" << RESET;
            }
            
            else if (sub_choice == "5" || sub_choice == "05" || sub_choice == "base64"){
                std::string input;

                std::cout << YELLOW << "[>]" << RESET << " Enter Base64-encoded input: ";
                std::getline(std::cin, input);

                decodeAndPrintBase64(input);
            }
            
            else if (sub_choice == "6" || sub_choice == "06" || sub_choice == "ROT13" || sub_choice == "rot13") {
                        std::string input;
                        std::cout << YELLOW << "[>] " << RESET << "Enter the text to ROT13 encode/decode: ";
                        cin.ignore(); // Clear any newline
                        getline(std::cin, input);

                        std::string result = applyROT13(input);

                        std::cout << BLUE << "_________________________________________________________________\n" << RESET;
                        std::cout << endl;
                        std::cout << GREEN << "[-] " << RESET << "Result (ROT13): " << GREEN << result << RESET << std::endl;
                        std::cout << BLUE << "_________________________________________________________________\n" << RESET;
            }

            else if (sub_choice == "7" || sub_choice == "07" || sub_choice == "Convertion" || sub_choice == "convertion") {
                            string conv_choice;

                            cout << BLUE << "______________________" << RESET<< GREEN << " Convertion Options "<< RESET << BLUE << "_______________________" << RESET << endl;
                            cout << endl;
                            cout << YELLOW << "[1]" << RESET << " Convert hex to decimal" << endl;
                            cout << BLUE << "_________________________________________________________________\n" << RESET;
                            cout << endl;
                            cout << YELLOW << "[>] " << RESET<< "Select an option: ";
                            cin >> conv_choice;
                            std::cin.ignore();
                            cout << endl;

                            if (conv_choice == "01" || conv_choice == "1"){
                                convert_hex_to_decimal();
                            }  
            }

            else if (sub_choice == "8" || sub_choice == "08" || sub_choice == "Framework" || sub_choice == "framework") {
                   string framework_choice;

                    cout << BLUE << "______________________" << RESET<< GREEN << " Framework Options "<< RESET << BLUE << "________________________" << RESET << endl;
                    cout << endl;
                    cout << YELLOW << "[1]" << RESET << " Popular Cryptography Websites" << endl;
                    cout << YELLOW << "[2]" << RESET << " Popular Cryptography Tools" << endl;
                    cout << YELLOW << "[3]" << RESET << " Popular Cryptography CTF Tools" << endl;
                    cout << YELLOW << "[4]" << RESET << " Popular CTF Sites" << endl;
                    cout << BLUE << "_________________________________________________________________\n" << RESET;
                    cout << endl;
                    cout << YELLOW << "[>] " << RESET<< "Select an option: ";
                    cin >> framework_choice;
                    cout << endl;  
                    
                    if (framework_choice == "1") {
                            showPopularWebsites();
                    } 
                    
                    else if (framework_choice == "2") {
                                showPopularCryptoTools();
                    } 
                    
                    else if (framework_choice == "3") {
                                showPopularCTFTools();
                    } 
                    
                    else if (framework_choice == "4") {
                                showPopularCTFSites();  // Call the new function
                    } 
                    
                    else {
                            cout << RED << "[!] Invalid option selected." << RESET << endl;
                    }
            }

            else {
                    cout << RED << "[x] " << RESET << "Invalid choice, please try again." << endl;
                    cout << endl;
            }

        }

        else {
            cout << RED << "[x] " << RESET << "Invalid Option Selected" << endl;
        }

        char repeat;
        cout << endl;
        cout << ORANGE << "[?] " RESET << "Return to main menu? (" << GREEN << "y" << RESET << "/" << RED << "n" << RESET << "): ";
        cin >> repeat;
        cout << endl;

        running = (repeat == 'y' || repeat == 'Y');
    }

    return 0;
}
