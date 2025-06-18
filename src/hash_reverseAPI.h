#ifndef HASH_API_REVERSE_H
#define HASH_API_REVERSE_H

#include <string>

// Reverses a hash using the md5decrypt.net API.
// Parameters:
//   - hash: the hash string to reverse
//   - hashType: the hash type, e.g. "md5", "sha1", "sha256", etc.
// Returns:
//   - The reversed string if found, or a message like "No result from API."
std::string reverseHashAPI(const std::string& hashing, const std::string& hashingType);

#endif // HASH_API_REVERSE_H
