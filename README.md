<p align="left">
  <img src="logo.png" alt="sokonalysis logo" width="280"/>
</p>

###### The Cipher Toolkit Build For All Skill Levels 




https://github.com/user-attachments/assets/f8731b3c-3f81-4b6d-8e3c-9796764cf3f9




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
<img width="1920" height="1032" alt="image" src="https://github.com/user-attachments/assets/b2da5e03-4f69-43ac-8993-b23c12037c55" />


## Download
### Linux
````bash
wget https://github.com/sokonalysis/sokonalysis/releases/download/v4.0.0/sokonalysis_4.0.0_all.deb && sudo dpkg -i sokonalysis_4.0.0_all.deb
````
#### Execution 
````bash
sokonalysis
````
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/1441a46e-74ef-4e79-ad86-1300226304f2" />


### Windows
#### Download and Installation 
1. **Download** the **.exe** installer via **GitHub Releases**
2. Select your preferred installation mode
   
   <img width="259" height="181" alt="0" src="https://github.com/user-attachments/assets/05999401-98b4-4612-8ba8-75c33d2e4bbb" />

3. Select the destination path where to store the application files or leave it as default
   
   <img width="493" height="379" alt="0 1" src="https://github.com/user-attachments/assets/9209c239-c3cf-4fdc-84bb-93e7a43d6bdc" />

4. Start menu folder
   
   <img width="491" height="375" alt="0 2" src="https://github.com/user-attachments/assets/9d9f8835-5ee4-460d-9093-4cdb06fc6e0b" />

5. Double click on the .exe installer, tick **Create desktop a shortcut** and **press Next**

   <img width="494" height="379" alt="1" src="https://github.com/user-attachments/assets/036b18cf-34c7-4644-bc13-c1e7f3fe5204" />


6. Press **Install**
   
   <img width="493" height="377" alt="2" src="https://github.com/user-attachments/assets/e335d627-a73f-4a3b-baca-c830b3583d78" />


7. Wait for the installation process to finish
   
   <img width="491" height="378" alt="3" src="https://github.com/user-attachments/assets/e8c2fa7a-1f7a-44f3-8230-865c959b00d4" />


8. Press **Finish**
   
   <img width="493" height="380" alt="4" src="https://github.com/user-attachments/assets/13eee142-2b3f-4fc9-8532-029dafaccd42" />


#### Starting The Application 
1. Double click on the **Desktop shortcut** or search for sokonalysis then press **Open**

   <img width="380" height="397" alt="Open App" src="https://github.com/user-attachments/assets/43ee7519-7b16-470d-b8f3-b53178b4f7fb" />

2. Wait for the application to finish loading

   <img width="957" height="540" alt="Loading" src="https://github.com/user-attachments/assets/3a3f4d1f-070f-4ae8-b566-49cc1e49cde4" />





   


   


