// attack.cpp

#include "coppersmith.h"
#include <fstream>
#include <cstdlib>
#include <iostream>

void runCoppersmithAttack(const std::string& n, const std::string& e, const std::string& c, const std::string& knownPrefix) {
    // Write to temp input file
    std::ofstream fout("attack_input.txt");
    fout << n << "\n" << e << "\n" << c << "\n" << knownPrefix << std::endl;
    fout.close();

    // Run Sage script
    std::cout << "[*] Running Sage..." << std::endl;
    int ret = system("sage coppersmith_attack.sage < attack_input.txt");
    if (ret != 0) {
        std::cerr << "[!] Sage script failed!" << std::endl;
    }
}
