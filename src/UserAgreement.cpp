// UserAgreement.cpp
#include "UserAgreement.h"
#include <iostream>
#include <fstream>

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

using namespace std;

const string AGREEMENT_FILE = "agreement.txt";

bool UserAgreement::checkAgreement() {
    ifstream file(AGREEMENT_FILE);
    string status;
    if (file.is_open()) {
        getline(file, status);
        file.close();
        return status == "ACCEPTED";
    }
    return false;
}

void UserAgreement::displayAgreement() {
    cout << BLUE << "\n__________________ " << GREEN << "sokonalysis User Agreement" << RESET << BLUE << " ___________________\n"<< RESET;
    cout << endl;
    cout << "This tool is for EDUCATIONAL and ETHICAL use only.\n";
    cout << "Do " << RED << "NOT" << RESET << " use this software for any malicious, unauthorized,\n";
    cout << "or illegal purposes.\n";
    cout << BLUE << "_________________________________________________________________\n" << RESET;
    cout << endl;
    cout << YELLOW << "[>]" << RESET << " Do you agree to these terms? (" << GREEN << "yes" << RESET << "/" << RED << "no" << RESET << "): ";
    string input;
    cin >> input;

    if (input == "yes" || input == "Yes" || input == "YES") {
        ofstream file(AGREEMENT_FILE);
        file << "ACCEPTED";
        file.close();
        cout << "\nThank you. Agreement accepted.\n\n";
    } else {
        cout << "\nYou must accept the terms to use sokonalysis. Exiting...\n";
        exit(0);
    }
}
