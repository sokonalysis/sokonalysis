#ifndef HASH_REVERSE_API_H
#define HASH_REVERSE_API_H

#include <string>

// Reverses a hash using the md5decrypt.net API.
// Parameters:
//   - hash: the hash string to reverse
//   - hashType: the type of hash (e.g., "md5", "sha1", "sha256", etc.)
// Returns:
//   - The reversed value if found, or an error message.
std::string reverseHashViaAPI(const std::string& hash, const std::string& hashType);

#endif // HASH_REVERSE_API_H
