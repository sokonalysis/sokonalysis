// rsaCTF.h
#ifndef RSACTF_H
#define RSACTF_H

#include <string>
#include <cryptlib.h>
#include <integer.h>

std::string decryptRSA(const std::string& c_str, const std::string& e_str, const std::string& p_str, const std::string& q_str);

#endif // RSACTF_H
