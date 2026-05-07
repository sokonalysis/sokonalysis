<p align="left">
  <img src="logo.png" alt="sokonalysis logo" width="280"/>
</p>

###### The Cipher Toolkit Build For All Skill Levels 

# About
sokonalysis from the word cryptanalysis is a cryptographic tool developed by Soko James and it seeks to decrypt encrypted messages or break cryptographic systems with or without the secret key. Meant for University Students, Capture The Flag (CTF) competitions and Organizations to apply cryptography as a field. Officially released on 8th September, 2025 and copyrighted under Kapasa Makasa University till 1st September, 2026.


# Table of Contents
- [Command Line Interface (CLI)](#command-line-interface-cli)
  - [Windows](#windows)
  - [Linux](#linux)
- [Graphical User Interface (GUI)](#graphical-user-interface-gui)
  - [Linux](#linux)

# Command Line Interface (CLI)
<img width="1280" height="720" alt="image" src="https://github.com/user-attachments/assets/8230389e-4e25-40f9-b336-ba80e006174b" />

## Windows
### MSYS2
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
#### Clone 
```bash
git clone https://github.com/sokonalysis/sokonalysis.git
```
```bash
cd sokonalysis
````
````bash
cd src
````
#### Wordlist
````bash
curl -L -o wordlist.txt https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt
````
#### Crypto++
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
### Clone
```bash
git clone https://github.com/sokonalysis/sokonalysis.git
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
sudo apt install libgmp-dev libmpfr-dev libmpc-dev
````
````bash
sudo apt install nlohmann-json3-dev
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

### Wordlist
````bash
curl -L -o wordlist.txt https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt
````

### Build & Run
````bash
g++ -I/usr/include/cryptopp -std=c++17 *.cpp -lcryptopp -lssl -lcrypto -lcurl -lgmp -lgmpxx -o sokonalysis
````
OR
````bash
g++ -Icryptopp -std=c++17 *.cpp -lcryptopp -lssl -lcrypto -lcurl -lgmp -lgmpxx -o sokonalysis
````
````bash
./sokonalysis
````
<img width="1280" height="720" alt="image" src="https://github.com/user-attachments/assets/aac1ba4f-aa08-4322-9db6-8dba8b7a5b4d" />


# Graphical User Interface (GUI)
<img width="1280" height="720" alt="image" src="https://github.com/user-attachments/assets/272ed250-e50e-464e-8b9c-c7517271a5a2" />

#### Linux
````bash
wget https://github.com/sokonalysis/sokonalysis/releases/download/v3.5.0/sokonalysis_3.5.0_all.deb && sudo dpkg -i sokonalysis_3.5.0_all.deb
````
#### Execution 
````bash
sokonalysis
````
<img width="1280" height="720" alt="image" src="https://github.com/user-attachments/assets/946e5858-feb2-4888-bb46-820cfc32b5e3" />


