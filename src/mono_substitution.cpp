#include "mono_substitution.h"
#include <iostream>
#include <cstdlib>

#ifdef _WIN32
#include <windows.h>
#include <shellapi.h>
#endif

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

void SubstitutionSolver::openSolverInBrowser() {
    const char* url = "https://www.guballa.de/substitution-solver";

    std::cout << std::endl;

    std::cout << GREEN << "[-]" << RESET << " Opening the Guballa Substitution Solver in your default browser...\n";

#ifdef _WIN32
    // Windows: use ShellExecuteA
    ShellExecuteA(NULL, "open", url, NULL, NULL, SW_SHOWNORMAL);
#elif __APPLE__
    // macOS: use 'open' command
    std::string command = "open ";
    command += url;
    system(command.c_str());
#else
    // Linux/Unix: use xdg-open
    std::string command = "xdg-open ";
    command += url;
    system(command.c_str());
#endif

    std::cout << RED << "[!]" << RESET << " Please paste your ciphertext there.\n\n";
}
