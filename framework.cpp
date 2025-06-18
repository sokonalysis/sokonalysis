// framework.cpp
#include "framework.h"
#include <iostream>
using namespace std;

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


void showPopularWebsites() {
    cout << BLUE << "_________________________________________________________________\n" << RESET;
    cout << endl;
    cout << "[-] https://cryptohack.org/\n";
    cout << "[-] https://ctflearn.com/\n";
    cout << "[-] https://cryptopals.com/\n";
    cout << "[-] https://www.root-me.org/\n";
    cout << BLUE << "_________________________________________________________________\n" << RESET;
}

void showPopularCryptoTools() {
    cout << BLUE << "_________________________________________________________________\n" << RESET;
    cout << endl;
    cout << GREEN << "[-]" << RESET << " CyberChef        " << GREEN << "https://gchq.github.io/CyberChef" << RESET << endl;
    cout << GREEN << "[-]" << RESET << " Hashcat          " << GREEN << "https://hashcat.net" << RESET << endl;
    cout << GREEN << "[-]" << RESET << " John the Ripper  " << GREEN << "https://www.openwall.com/john" << RESET << endl;
    cout << GREEN << "[-]" << RESET << " GnuPG            " << GREEN << "https://gnupg.org" << RESET << endl;
    cout << GREEN << "[-]" << RESET << " OpenSSL          " << GREEN << "https://www.openssl.org" << RESET << endl;
    cout << BLUE << "_________________________________________________________________\n" << RESET;
}

void showPopularCTFTools() {
    cout << BLUE << "_________________________________________________________________\n" << RESET;
    cout << endl;
    cout << GREEN << "[-]" << RESET << " CyberChef        " << GREEN << "https://gchq.github.io/CyberChef" << RESET << endl;
    cout << GREEN << "[-]" << RESET << " dcode            " << GREEN << "https://www.dcode.fr/cipher-identifier" << RESET << endl;
    cout << GREEN << "[-]" << RESET << " Hashcat          " << GREEN << "https://hashcat.net" << RESET << endl;
    cout << GREEN << "[-]" << RESET << " John the Ripper  " << GREEN << "https://www.openwall.com/john" << RESET << endl;
    cout << GREEN << "[-]" << RESET << " RsaCtfTool       " << GREEN << "https://github.com/RsaCtfTool/RsaCtfTool" << RESET << endl;
    cout << GREEN << "[-]" << RESET << " factordb         " << GREEN << "https://github.com/ihebski/factordb" << RESET << endl;
    cout << GREEN << "[-]" << RESET << " OpenSSL          " << GREEN << "https://www.openssl.org" << RESET << endl;
    cout << BLUE << "_________________________________________________________________\n" << RESET;
}

void showPopularCTFSites() {
    cout << BLUE << "_________________________________________________________________\n" << RESET;
    cout << endl;
    cout << GREEN << "[-]" << RESET << " Hack The Box  " << GREEN << "https://www.hackthebox.com" << RESET << endl;
    cout << GREEN << "[-]" << RESET << " TryHackMe     " << GREEN << "https://tryhackme.com" << RESET << endl;
    cout << GREEN << "[-]" << RESET << " picoCTF       " << GREEN << "https://picoctf.org" << RESET << endl;
    cout << GREEN << "[-]" << RESET << " CyberTalents  " << GREEN << "https://cybertalents.com/" << RESET << endl;
    cout << GREEN << "[-]" << RESET << " CTFtime       " << GREEN << "https://ctftime.org" << RESET << endl;
    cout << GREEN << "[-]" << RESET << " Root-Me       " << GREEN << "https://www.root-me.org" << RESET << endl;
    cout << BLUE << "_________________________________________________________________\n" << RESET;
}
