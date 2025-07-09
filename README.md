# sokonalysis

<p align="left">
  <img src="logo.png" alt="sokonalysis logo" width="200"/>
</p>

###### The Cipher Toolkit Build For All Skill Levels 

## About
sokonalysis from the word cryptanalysis is a cryptographic tool developed by Soko James and it seeks to decrypt encrypted messages or break cryptographic systems with or without the secret key. Meant for University Students, Capture The Flag (CTF) competitions and Organizations to apply cryptography as a field.

## Table of Content
- [Requirements](#Requirements)
- [Windows](#Windows)
- [Linux](#Linux)
- [Usage](#Usage)

## Requirements
The file named **wordlist.txt** is needed for local wordlist for the hashing algorithms md5, sha1 and sha256 but if you wish to customize it, add your own text in the same text file and keep it in the same folder as the tool.

## Windows
### Dependencies
#### MSYS2
Download [MSYS2](https://github.com/msys2/msys2-installer/releases/download/2024-12-08/msys2-x86_64-20241208.exe)
Install MSYS2 and run the following command:
````bash
pacman -Syu
````
```bash
pacman -Su
````
````bash
pacman -S base-devel mingw-w64-x86_64-toolchain git
````
   
#### MSYS2 MINGW64 Terminal
````bash
pacman -S mingw-w64-x86_64-gcc
````
```bash
pacman -S mingw-w64-x86_64-nlohmann-json
````
````bash
pacman -S mingw-w64-x86_64-gmp
````
````bash
pacman -S mingw-w64-x86_64-curl
````
````bash
pacman -S mingw-w64-x86_64-openssl
````
```bash
git clone https://github.com/SokoJames/sokonalysis.git
```
```bash
cd sokonalysis
````
````bash
cd src
````
````bash
pacman -S --needed make git
````
````bash
git clone https://github.com/weidai11/cryptopp.git
````
````bash
cd cryptopp
````
````bash
make CXX=g++ -j$(nproc)
````
````bash
cd ..
````

### Build & Run
````bash
g++ -Icryptopp -std=c++17 *.cpp -lcryptopp -lssl -lcrypto -lcurl -lgmp -lgmpxx -o sokonalysis
````
````bash
./sokonalysis
````
   
## Linux   
### Download
```bash
git clone https://github.com/SokoJames/sokonalysis.git
```
```bash
cd sokonalysis
````
````bash
cd src
````

### Requirements
````bash
sudo apt update
````
````bash
sudo apt install libcrypto++-dev libcrypto++-doc libcrypto++-utils
````
````bash
sudo apt install libcrypto++-dev libssl-dev libcurl4-openssl-dev libgmp-dev libgmpxx4ldbl g++
````
````bash
mkdir -p external/nlohmann
````
````bash
wget -O external/nlohmann/json.hpp https://raw.githubusercontent.com/nlohmann/json/develop/single_include/nlohmann/json.hpp
````
### Build & Run
````bash
g++ -I/usr/include/cryptopp -Iexternal -std=c++17 *.cpp -lcryptopp -lssl -lcrypto -lcurl -lgmp -lgmpxx -o sokonalysis
````
````bash
./sokonalysis
````

## Usage
<img width="373" alt="Image" src="https://github.com/user-attachments/assets/25293170-ed1f-473c-9a4a-ef03d4664221" />

[Official sokonalysis YouTube Guide Playlist](https://youtube.com/playlist?list=PLbkdoTM3A8aOFijcnaxCZGhZklM5RsbaL&si=Yoo6r6xL3Y5DtohM)

1. ## University Level
   University students taking Cryptography as a course can utilize option 1 – 4 to automate their work. You don’t need internet connection (except options involving APIs or external websites) to perform these tasks but just some questions you can utilize. This tool will act as an offline calculator to verify the answers after a student 
solves a question manually.
   Lets take an RSA example from Kapasa Makasa University CYS110 2025 Test 1;
   
   a) You have received a message UTLAIKNP encrypted with the key (33,7). Find the private keys that should be used to decrypt the message and work out the clear text.

   `STEP 1` <br>
   Utilize option 8 to check the help menu and try to understand the RSA algorithm.

   <img width="371" alt="Image" src="https://github.com/user-attachments/assets/179df9b0-22d6-4f3e-8bf0-0d8eb71318f2" />

   `STEP 2` <br>
   Based on the encryption key given (33,7), we can conclude to say that the Public Key (n,e) is n = 33 and e = 7. Now, we compute n we get the product of p and q, for which they are two large prime numbers such as 11 and 3 which gives us 33. Let's now proceed to the RSA algorithm by selecting option 2.

   <img width="368" alt="Image" src="https://github.com/user-attachments/assets/01fc4a88-1900-4f21-805f-764b0af520ed" />

   `STEP 3` <br>
   Now, let's assume as if we are encrypting a message with the given Public Key (33,7) so that we can retrive the Private Key (n,d).

   <img width="364" alt="Image" src="https://github.com/user-attachments/assets/63aebc57-f8ed-4911-a08e-4a6ceb2bb131" />

   `STEP 4` <br>
   There we go, we've obtained the Private Key (33,3). Restart the program, welcome back!!! Let's utilize option 4 to convert the cipher text letters to numbers because the program can only decryp numerical values.

   <img width="368" alt="Image" src="https://github.com/user-attachments/assets/761da374-b013-4234-afac-c101fac6015a" />

   <br>
   
   <img width="368" alt="Image" src="https://github.com/user-attachments/assets/415199e6-7473-4e17-94c6-8af600d24d31" />

   `STEP 5` <br>
   At this point we can decode the given cipher text by following the previsious steps but selecting the decryption option.

   <img width="465" alt="Image" src="https://github.com/user-attachments/assets/f9d3c389-3d6d-4be0-a072-a42c4f67f7aa" />

3. ## CTF Level
   Cryptography is a popular category in most Capture The Flag platforms like [Hack The Box (HTB)](https://account.hackthebox.com/login), [PicoCTF](https://play.picoctf.org/), [CyberChef](https://cybertalents.com/) etc.. sokonalysis can be used to solve these challenges, but with v2.2 only few algorithms are working. sokonalysis will also provide a framework that will link the user to all popular Cryptographic tools used for CTF, thereby reducing the time of finding the right tools to use.

   <img width="369" alt="Image" src="https://github.com/user-attachments/assets/b8214bc3-b6eb-4ac7-b791-fe7b1bc60b79" />

    Let’s jump into these challenges!!!

   ### [No Padding, no problem](https://play.picoctf.org/practice/challenge/154?category=2&page=3&search=) <br>
   `STEP 1` <br>
   Connect to the challenge server with the command nc mercury.picoctf.net 42248 in Linux or ncat mercury.picoctf.net 42248 on Windows CMD if you have Nmap - Zenmap GUI installed.

   <img width="675" alt="Image" src="https://github.com/user-attachments/assets/5768dd50-c1cb-455a-8281-68ce342dd36f" />

   `STEP 2` <br>
   Select option 1 to view RSA options.
   
   <img width="375" alt="Image" src="https://github.com/user-attachments/assets/179b2571-d930-4c71-816e-69fb9eaad423" />

   `STEP 3` <br>
   Select option 13 and enter the given values for n, e and c.

   <img width="664" alt="Image" src="https://github.com/user-attachments/assets/9fd35805-6f93-4d88-a89a-d8e614f4a074" />

   `STEP 4` <br>
   Give the server the modified cipher text to decrypt.

   <img width="674" alt="Image" src="https://github.com/user-attachments/assets/151e94dd-2e12-4784-a936-b4d7f594ce80" />

   `STEP 5` <br>
   Finally, decrypt the cipher to get the flag with the new cipher text from the server.

   <img width="664" alt="Image" src="https://github.com/user-attachments/assets/18aadd49-b817-4f7c-bfca-b1a3e229169c" />
   
5. ## Advanced Level 

# Supported Algorithms

| **Symmetric**                         | **Asymmetric**     | **Hashing**           | **Capture The Flag (CTF)**| **Advanced Cryptography** |
|---------------------------------------|--------------------|-----------------------|---------------------------|---------------------------|
| Caesar Cipher                         | RSA                | MD5                   | RSA                       |                           |
| Transposition Cipher                  |                    | SHA                   | FactorDB                  |                           |
| Hill Cipher                           |                    |                       | Substitution Cipher       |                           |
|                                       |                    |                       | Morse Code                |                           |
|                                       |                    |                       | Base64 Decoder            |                           |                               |                                       |                    |                       | ROT13                     |                           |   
|                                       |                    |                       |                           |                           |
|

## Contributors
Thanks to everyone who has contributed!
[![](https://contrib.rocks/image?repo=SokoJames/sokonalysis)](https://github.com/SokoJames/sokonalysis/graphs/contributors)

