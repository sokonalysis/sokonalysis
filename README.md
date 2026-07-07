<p align="left">
  <img src="logo.png" alt="sokonalysis logo" width="280"/>
</p>

###### The Cipher Toolkit Build For All Skill Levels 



# Command Line Interface (CLI)
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/56d9f410-a181-487b-b16a-bb2e7679b6e5" />



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
<img width="1430" height="932" alt="image" src="https://github.com/user-attachments/assets/a5339483-1158-471c-ac02-aadc3c03e53b" />


## Download
### Linux
````bash
wget https://github.com/sokonalysis/sokonalysis/releases/download/v3.5.0/sokonalysis_3.5.0_all.deb && sudo dpkg -i sokonalysis_3.5.0_all.deb
````
#### Execution 
````bash
sokonalysis
````
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/f25c499a-e9af-4ade-860f-c85dc0c55d78" />



### Windows
1. Download the .exe installer via GitHub Releases
2. Double click on the .exe installer, tick **Create desktop a shortcut** and **press Next**
   
   <img width="589" height="451" alt="1" src="https://github.com/user-attachments/assets/bbc4e898-cfcd-4444-b75c-78522397916e" />

3. Press **Install**
   
   <img width="586" height="451" alt="2" src="https://github.com/user-attachments/assets/23ebed2b-cc56-4ee5-be3a-f7d1e362d3b1" />

4. Wait for the installation process to finish
   
   <img width="587" height="453" alt="3" src="https://github.com/user-attachments/assets/f4a44c93-90e1-43bf-a82c-812c7d2d8cd8" />

5. Press **Finish**
   
   <img width="590" height="453" alt="4" src="https://github.com/user-attachments/assets/f1fc0431-875a-4bc1-99bf-9c715ddf45a0" />





   


   


