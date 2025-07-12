// DiffieHellman.h

#ifndef DIFFIEHELLMAN_H
#define DIFFIEHELLMAN_H

class DiffieHellman {
private:
    int g;      // base
    int p;      // modulus
    int secret; // private key

public:
    DiffieHellman(int base, int modulus, int privateKey);
    int generatePublicKey();
    int computeSharedKey(int receivedPublicKey);
};

#endif // DIFFIEHELLMAN_H
