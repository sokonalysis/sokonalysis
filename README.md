# sokonalysis v2.2

<p align="left">
  <img src="logo.png" alt="sokonalysis logo" width="200"/>
</p>

###### The Cipher Toolkit Build For All Skill Levels 

## About
sokonalysis from the word Cryptanalysis is a Cryptographic tool developed by Soko James and it seeks to decrypt encrypted messages or break cryptographic systems with or without the secret key.

## Table of Content
- [Dependencies](#Dependencies)
- [Installation](#Installation)
- [Usage](#Usage)

## Dependencies
**NOTE:** Keep all the files in the same folder sokonalysis-main for it to execute without any issues, failure to that you will need to install the dependancies on your machine, that includes;
1. `libgcc_s_seh-1.dll`
2. `libstdc++-6.dll`
3. `libwinpthread-1.dll`
4. `libbrotlicommon.dll`
5. `libbrotlidec.dll`
6. `libcrypto-3-x64.dll`
7. `libcurl-4.dll`
8. `libgmp-10.dll`
9. `libgmpxx-4.dll`
10. `libiconv-2.dll`
11. `libidn2-0.dll`
12. `libintl-8.dll`
13. `libnghttp2-14.dll`
14. `libnghttp3-9.dll`
15. `libpsl-5.dll`
16. `libssh2-1.dll`
17. `libssl-3-x64.dll`
18. `libunistring-5.dll`
19. `libzstd.dll`
20. `zlib1.dll`
21. Lastly, the file named **md5wordlist.txt** is needed for local wordlist for the hashing algorithms md5, sha1 and sha256 but if you wish to customize it, add your own wordlist and name it md5wordlist.txt in the same folder as the tool.

## Installation
### Windows
1. Click on **Code** → **Download ZIP**
2. Go to your downloads and unzip **sokonalysis-main.zip**
3. Open the unzipped folder and double click on **sokonalysis.exe**
4. Enjoy!!!
   
### Linux
1. Open your Linux Terminal
2. Enter the command `git clone https://github.com/SokoJames/sokonalysis.git` to download sokonalysis
3. Change the directory with the command `cd sokonalysis`
4. Give the tool executable permissions with the command `chmod +x sokonalysis`
5. Run the tool with the command `./sokonalysis`
6. Enjoy!!!

## Usage
<img width="373" alt="Image" src="https://github.com/user-attachments/assets/25293170-ed1f-473c-9a4a-ef03d4664221" />

1. ## University Level
   University students taking Cryptography as a course can utilize option 1 – 4 to automate their work. You don’t need internet connection (except options involving APIs or external websites) to perform these tasks but just some questions you can utilize. This tool will act as an offline calculator to verify the answers after a student 
solves a question manually.
Lets take an RSA example from Kapasa Makasa University CYS110 2025 Test 1;

a) You have received a message UTLAIKNP encrypted with the key (33,7). Find the private keys that should be used to decrypt the message and work 
out the clear text.

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
   
   
5. ## Advanced Level 

