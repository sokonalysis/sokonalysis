# sokonalysis

<p align="left">
  <img src="logo.png" alt="sokonalysis logo" width="200"/>
</p>

###### The Cipher Toolkit Build For All Skill Levels 

## About
sokonalysis from the word cryptanalysis is a cryptographic tool developed by Soko James and it seeks to decrypt encrypted messages or break cryptographic systems with or without the secret key. Meant for University Students, Capture The Flag (CTF) competitions and Organizations to apply cryptography as a field. Officially released on 8th September, 2025 and copyrighted under Kapasa Makasa University till 1st September, 2026.


## Table of Content
- [Requirements](#Requirements)
- [Download](#Download)
- [Update](#Update)
- [Usage](#Usage)


## Requirements
### Wordlist
The file named **wordlist.txt** is needed for local/default wordlist for the hashing algorithms md5, sha1 and sha256, and cracking passwords with John The Ripper but if you wish to customize it, add your own wordlist in the /sokonalysis/src directory and rename it to wordlist.txt.

### Linux Tools
#### impacket-secretsdump
This tool is used to create a merged hash of a Windows user account from the **SYSTEM** and **SAM** file provided by the user in Advanced Cryptography under Crack Operating Systems User Passwords.

````bash
sudo apt install impacket-scripts -y
````
#### John The Ripper
This tool is used to crack protected file/document passwords provided by the users by using the sub-tools such as **zip2john** (cracking Zipped files), **rar2john** (cracking RAR archived files), **7z2john** (cracking 7z files), **hccap2john** (cracking Wi-Fi passwords) and **bitlocker2john** (cracking Windows Bitlocker) which extract the hash for john to crack.

````bash
sudo apt install john -y
````
#### Aircrack-ng
This tool is used to convert the **.cap** handshake file provided by the user to **.hccap** file that **hccap2john** will extract the hash from for **john** to crack the Wi-Fi password.

````bash
sudo apt install aircrack-ng -y
````

## Download 
### Windows
**NOTE:** If you don't want to use MSYS2, you can skip these installation guide and use the Linux command if you are using Windows Subsystem for Linux (WSL). Below are some instructions on how to install WSL.

#### WSL
##### Virtualization 
Check Virtualization Status by pressing **Ctrl + Shift + Esc** on you keyboard and navigate to **Performance** and if not enabled, open Command Prompt (CMD) as an Administrator and type the command below, or shutdown your PC and go to BIOS Setup under Virtualization Technology and enable it.
```bash
shutdown /r /fw /t 2
````

#### Download 
Run Windows PowerShell as an Administrator and enter the command: 
```bash
wsl –install
````
```bash
wsl --install -d kali-linux
````

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
   
##### MSYS2 MINGW64 Terminal
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
##### Download 
```bash
git clone https://github.com/sokonalysis/sokonalysis.git
```
```bash
cd sokonalysis
````
````bash
cd src
````
##### Wordlist
````bash
curl -L -o wordlist.txt https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt
````
##### Crypto++
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

#### Build & Run
````bash
g++ -Icryptopp -std=c++17 *.cpp -lcryptopp -lssl -lcrypto -lcurl -lgmp -lgmpxx -o sokonalysis
````
OR
````bash
g++ -I/usr/include/cryptopp -std=c++17 *.cpp -lcryptopp -lssl -lcrypto -lcurl -lgmp -lgmpxx -o sokonalysis
````
````bash
./sokonalysis
````

   
### Linux   
#### Download
```bash
git clone https://github.com/sokonalysis/sokonalysis.git
```
```bash
cd sokonalysis
````
````bash
cd src
````

#### Requirements
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
sudo apt install libgmp-dev libmpfr-dev libmpc-dev
````
````bash
sudo apt install nlohmann-json3-dev
````

#### Virtual Environment 
```bash
python3 -m venv pythonvenv
```
```bash
source pythonvenv/bin/activate
````
````bash
pip install -r requirements.txt
````

#### Wordlist
````bash
curl -L -o wordlist.txt https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt
````

#### Build & Run
````bash
g++ -I/usr/include/cryptopp -std=c++17 *.cpp -lcryptopp -lssl -lcrypto -lcurl -lgmp -lgmpxx -o sokonalysis
````
````bash
./sokonalysis
````
<img width="801" height="369" alt="Image" src="https://github.com/user-attachments/assets/e820ae6f-bb1a-47c4-aa63-d9f53d1b77b3" />



### GUI
````bash
python3 sokonalysis_gui.py
````
<img width="796" height="616" alt="image" src="https://github.com/user-attachments/assets/db8544e8-a761-421c-b685-8d5d73330aae" />


## Update
```bash
cd sokonalysis
````
````bash
cd src
````
```bash
git pull
````

## Usage

[Official sokonalysis YouTube Guide Playlist](https://youtube.com/playlist?list=PLbkdoTM3A8aOFijcnaxCZGhZklM5RsbaL&si=Yoo6r6xL3Y5DtohM)

1. ### University Level
   University students taking Cryptography as a course can utilize option 1 – 4 to automate their work. You don’t need internet connection (except options involving APIs or external websites) to perform these tasks but just some questions you can utilize. This tool will act as an offline calculator to verify the answers after a student 
solves a question manually.
   Lets take an RSA example from Kapasa Makasa University CYS110 2025 Test 1;
   
   a) You have received a message UTLAIKNP encrypted with the key (33,7). Find the private keys that should be used to decrypt the message and work out the clear text.

   `STEP 1` <br>
   Utilize option 2 and select option 3 to check the help menu and try to understand the RSA algorithm.

   <img width="796" height="616" alt="image" src="https://github.com/user-attachments/assets/e992e13a-3065-4bdd-84a3-3479c085b525" />


   `STEP 2` <br>
   Based on the encryption key given (33,7), we can conclude to say that the Public Key (n,e) is n = 33 and e = 7. Now, we compute n we get the product of p and q, for which they are two large prime numbers such as 11 and 3 which gives us 33. Let's now proceed to the RSA algorithm by selecting option 2.

   <img width="800" height="623" alt="image" src="https://github.com/user-attachments/assets/c2a93f04-7967-4844-beb0-1ef42fb2e42f" />


   `STEP 3` <br>
   Now, let's assume as if we are encrypting a message with the given Public Key (33,7) so that we can retrive the Private Key (n,d).

   <img width="828" height="652" alt="image" src="https://github.com/user-attachments/assets/a821f78f-d040-4c9e-9f4b-88ffd4fa0f00" />


   `STEP 4` <br>
   There we go, we've obtained the Private Key (33,3). Restart the program, welcome back!!! Let's utilize option 4 to convert the cipher text letters to numbers because the program can only decryp numerical values.

   <img width="796" height="654" alt="Image" src="https://github.com/user-attachments/assets/0a4d12e4-78ca-412c-88e8-9bc8c9ebd2e3" />
   
   <img width="801" height="382" alt="Image" src="https://github.com/user-attachments/assets/ca722b70-7c5e-45af-b35f-41c86c6d2132" />

   `STEP 5` <br>
   At this point we can decode the given cipher text by following the previsious steps but selecting the decryption option.

   <img width="801" height="309" alt="Image" src="https://github.com/user-attachments/assets/d0bb4f2e-0253-44d8-9094-17384e5a9b66" />

3. ### CTF Level
   Cryptography is a popular category in most Capture The Flag platforms like [Hack The Box (HTB)](https://account.hackthebox.com/login), [PicoCTF](https://play.picoctf.org/), [CyberTalents](https://cybertalents.com/), [ZedCTF](https://zedctf.web.app ) etc.. sokonalysis can be used to solve these challenges, but with v3.5 only few algorithms are working. sokonalysis will also provide a framework that will link the user to all popular Cryptographic tools used for CTF, thereby reducing the time of finding the right tools to use.

   <img width="828" height="652" alt="image" src="https://github.com/user-attachments/assets/dd14a234-c900-4131-82c8-e16b2116d195" />


    Let’s jump into these challenges!!!

   #### [No Padding, no problem](https://play.picoctf.org/practice/challenge/154?category=2&page=3&search=) <br>
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

5. ### Advanced Level
   #### Cracking Protected Documents
   Register your account on ZedCTF and practice the [John](https://zedctf.web.app/practice/multi/4qEkWQ2nTYT4GsiRnyPd) challenge to understand how to crack these Procted Files with passwords.
   
   ##### Zipped Files
   `STEP 1`
   Download the target [zip file](https://drive.google.com/file/d/185e7VWtPm-xEb0Xkv41WJjcKL_XZaPR_/view) and save the file in /sokonalysis/src/, run sokonalysis and select option number 5.

   <img width="828" height="652" alt="image" src="https://github.com/user-attachments/assets/4886fca0-f8a2-4075-a0f7-16dbdb679215" />

   `STEP 2`
   Select option number 1 then option number 2.

   <img width="828" height="652" alt="image" src="https://github.com/user-attachments/assets/610512e1-eef9-4a57-a70a-0940ce953758" />

   `STEP 3`
   Select the target zip file.

   <img width="828" height="652" alt="image" src="https://github.com/user-attachments/assets/904ed151-6058-402b-a31b-ac0e750809b2" />

   `STEP 4`
   Select your prefered options to crack the password.

   <img width="828" height="652" alt="image" src="https://github.com/user-attachments/assets/8951e3bc-b074-412f-9756-ebb9ceee0c7d" />

   ##### 7z Files
   `STEP 5`
   Extract the zipped folder with the cracked password, add the .7z file in /sokonalysis/src/, restart sokonalysis and go back on option number 5. Select option number 1 then option number 4 and lastly select the target .7z file.

   <img width="828" height="652" alt="image" src="https://github.com/user-attachments/assets/3fb04194-c52c-4f3e-b902-a6a2414d7715" />

   `STEP 6`
   Select your prefered options to crack the password.


   


## Supported Algorithms

| **Symmetric**                         | **Asymmetric**     | **Hashing**           | **Capture The Flag (CTF)**| **Advanced Cryptography**                                            |
|---------------------------------------|--------------------|-----------------------|---------------------------|----------------------------------------------------------------------|
| Caesar Cipher                         | RSA                | MD5                   | RSA                       |  Recover Microsoft Office forgotten passwords on protected docs      |
| Transposition Cipher                  | Diffie Hellman     | SHA                   | FactorDB                  |  Recover forgotten passwords on protected zip, 7z, pdf and RAR files |
| Hill Cipher                           |                    | lm                    | Substitution Cipher       |  Crack user account password (s) on both Linux and Windows           |
|                                       |                    | ntlm                  | Morse Code                |  Crack a Wi-Fi password using a captured handshake file              |
|                                       |                    | mysql                 | Base64 Decoder            |  Crack Windows BitLocker using an Image File                         |            |                                       |                    | ripemd160             | ROT13                     |                                                                      |   
|                                       |                    | whirlpool             | ChaCha20                  |                                                                      |
|                                       |                    |                       | Diffie-Hellman            |                                                                      |     
|                                       |                    |                       | AES                       |                                                                      |
|                                       |                    |                       | steghide                  |                                                                      |

