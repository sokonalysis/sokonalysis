# sokonalysis

<p align="left">
  <img src="logo.png" alt="sokonalysis logo" width="200"/>
</p>

###### The Cipher Toolkit Build For All Skill Levels 

## About
sokonalysis from the word cryptanalysis is a cryptographic tool developed by Soko James and it seeks to decrypt encrypted messages or break cryptographic systems with or without the secret key. Meant for University Students, Capture The Flag (CTF) competitions and Organizations to apply cryptography as a field. Officially released on 8th September, 2025 and copyrighted under Kapasa Makasa University till 1st September, 2026.

## Table of Content
- [Requirements](#Requirements)
- [Windows](#Windows)
- [Linux](#Linux)
- [Usage](#Usage)

## Requirements
The file named **wordlist.txt** is needed for local wordlist for the hashing algorithms md5, sha1 and sha256 but if you wish to customize it, add your own text in the same text file and keep it in the same folder as the tool.

## Collaborator 
For every git clone command on the download option, use these commands below if you have access to the repository.

````bash
ssh-keygen -t ed25519 -C "your-email@example.com"
````
````bash
cat ~/.ssh/id_ed25519.pub
````
1. Copy the full output (starts with ssh-ed25519).
2. Go to GitHub → Settings → SSH and GPG keys
3. Click “New SSH key”
4. Paste the public key
5. Give it a title (e.g., "sokonalysis SSH")
6. Click “Add SSH key”

````bash
ssh -T git@github.com
````
````bash
git clone git@github.com:sokonalysis/sokonalysis.git
````

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
git clone https://github.com/sokonalysis/sokonalysis.git
```
```bash
cd sokonalysis
````
````bash
cd src
````
````bash
curl -L -o wordlist.txt https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt
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
git clone https://github.com/sokonalysis/sokonalysis.git
```
```bash
cd sokonalysis
````
````bash
cd src
````

### Virtual Environment 
```bash
python3 -m venv pythonvenv
```
```bash
source pythonvenv/bin/activate
````
````bash
pip install -r requirements.txt
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
sudo apt install nlohmann-json3-dev
````
````bash
curl -L -o wordlist.txt https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt
````

### Build & Run
````bash
g++ -I/usr/include/cryptopp -std=c++17 *.cpp -lcryptopp -lssl -lcrypto -lcurl -lgmp -lgmpxx -o sokonalysis
````
````bash
./sokonalysis
````
<img width="801" height="369" alt="Image" src="https://github.com/user-attachments/assets/e820ae6f-bb1a-47c4-aa63-d9f53d1b77b3" />
<img width="802" height="537" alt="Image" src="https://github.com/user-attachments/assets/0e85c138-0a19-44d5-a13d-043db89b34a0" />

### GUI
````bash
python3 sokonalysis_gui.py
````
<img width="403" height="316" alt="Image" src="https://github.com/user-attachments/assets/75378425-eea7-4a1d-8a0e-cbfffd5750d0" />

<img width="402" height="314" alt="Image" src="https://github.com/user-attachments/assets/bb4c0440-b63e-48bf-85d4-20700fc5884d" />

## Usage

[Official sokonalysis YouTube Guide Playlist](https://youtube.com/playlist?list=PLbkdoTM3A8aOFijcnaxCZGhZklM5RsbaL&si=Yoo6r6xL3Y5DtohM)

1. ## University Level
   University students taking Cryptography as a course can utilize option 1 – 4 to automate their work. You don’t need internet connection (except options involving APIs or external websites) to perform these tasks but just some questions you can utilize. This tool will act as an offline calculator to verify the answers after a student 
solves a question manually.
   Lets take an RSA example from Kapasa Makasa University CYS110 2025 Test 1;
   
   a) You have received a message UTLAIKNP encrypted with the key (33,7). Find the private keys that should be used to decrypt the message and work out the clear text.

   `STEP 1` <br>
   Utilize option 8 to check the help menu and try to understand the RSA algorithm.

   <img width="798" height="572" alt="Image" src="https://github.com/user-attachments/assets/27a61ad7-6edb-4d9d-a3f9-d1dbba8ec67c" />

   `STEP 2` <br>
   Based on the encryption key given (33,7), we can conclude to say that the Public Key (n,e) is n = 33 and e = 7. Now, we compute n we get the product of p and q, for which they are two large prime numbers such as 11 and 3 which gives us 33. Let's now proceed to the RSA algorithm by selecting option 2.

   <img width="801" height="656" alt="Image" src="https://github.com/user-attachments/assets/debf131e-9541-446d-b755-931431f1a5a5" />

   `STEP 3` <br>
   Now, let's assume as if we are encrypting a message with the given Public Key (33,7) so that we can retrive the Private Key (n,d).

   <img width="796" height="197" alt="Image" src="https://github.com/user-attachments/assets/b71ce952-55c6-4d20-93dd-fc96083e2583" />

   `STEP 4` <br>
   There we go, we've obtained the Private Key (33,3). Restart the program, welcome back!!! Let's utilize option 4 to convert the cipher text letters to numbers because the program can only decryp numerical values.

   <img width="796" height="654" alt="Image" src="https://github.com/user-attachments/assets/0a4d12e4-78ca-412c-88e8-9bc8c9ebd2e3" />
   
   <img width="801" height="382" alt="Image" src="https://github.com/user-attachments/assets/ca722b70-7c5e-45af-b35f-41c86c6d2132" />

   `STEP 5` <br>
   At this point we can decode the given cipher text by following the previsious steps but selecting the decryption option.

   <img width="801" height="309" alt="Image" src="https://github.com/user-attachments/assets/d0bb4f2e-0253-44d8-9094-17384e5a9b66" />

3. ## CTF Level
   Cryptography is a popular category in most Capture The Flag platforms like [Hack The Box (HTB)](https://account.hackthebox.com/login), [PicoCTF](https://play.picoctf.org/), [CyberTalents](https://cybertalents.com/) etc.. sokonalysis can be used to solve these challenges, but with v2.2 only few algorithms are working. sokonalysis will also provide a framework that will link the user to all popular Cryptographic tools used for CTF, thereby reducing the time of finding the right tools to use.

   <img width="800" height="425" alt="Image" src="https://github.com/user-attachments/assets/9423dd1c-03d8-4ecd-8ecc-2de091b61ecf" />

    Let’s jump into these challenges!!!

   ### [No Padding, no problem](https://play.picoctf.org/practice/challenge/154?category=2&page=3&search=) <br>
   `STEP 1` <br>
   Connect to the challenge server with the command nc mercury.picoctf.net 42248 in Linux or ncat mercury.picoctf.net 42248 on Windows CMD if you have Nmap - Zenmap GUI installed.

   <img width="805" height="487" alt="Image" src="https://github.com/user-attachments/assets/fa4d0b0c-8ec0-42d2-948d-d57802dd2c77" />

   `STEP 2` <br>
   Select option 1 to view RSA options.
   
   <img width="798" height="646" alt="Image" src="https://github.com/user-attachments/assets/91190808-578a-40e2-83c1-1958e0fe03ae" />

   `STEP 3` <br>
   Select option 13 and enter the given values for n, e and c.

   <img width="801" height="639" alt="Image" src="https://github.com/user-attachments/assets/8de9aa23-db27-432a-aff8-962cf44cdb40" />

   `STEP 4` <br>
   Give the server the modified cipher text to decrypt.

   <img width="802" height="177" alt="Image" src="https://github.com/user-attachments/assets/8cedc9ad-826d-4dcd-89e5-f1d4c4ea022a" />

   `STEP 5` <br>
   Finally, decrypt the cipher to get the flag with the new cipher text from the server.

   <img width="801" height="227" alt="Image" src="https://github.com/user-attachments/assets/cb763413-c696-43e1-94e0-11c6703ea639" />
   
5. ## Advanced Level 

# Supported Algorithms

| **Symmetric**                         | **Asymmetric**     | **Hashing**           | **Capture The Flag (CTF)**| **Advanced Cryptography** |
|---------------------------------------|--------------------|-----------------------|---------------------------|---------------------------|
| Caesar Cipher                         | RSA                | MD5                   | RSA                       |                           |
| Transposition Cipher                  | Diffie Hellman     | SHA                   | FactorDB                  |                           |
| Hill Cipher                           |                    | lm                    | Substitution Cipher       |                           |
|                                       |                    | ntlm                  | Morse Code                |                           |
|                                       |                    | mysql                 | Base64 Decoder            |                           |                               |                                       |                    | ripemd160             | ROT13                     |                           |   
|                                       |                    | whirlpool             | ChaCha20                  |                           |
|                                       |                    |                       | Diffie-Hellman            |                           |
|                                       |                    |                       | AES                       |                           |

## Contributors
Thanks to everyone who has contributed!
![Contributors](https://img.shields.io/github/contributors/SokoJames/sokonalysis)
[![](https://contrib.rocks/image?repo=SokoJames/sokonalysis)](https://github.com/SokoJames/sokonalysis/graphs/contributors)

