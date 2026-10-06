# Developers Only
## Tools
### Linux
All the commands must be entered on the Terminal

## Windows 
All the commands must be entered on [Git Bash](https://git-scm.com/install/windows)

## VSCode 
The project folder should be accessed in [VScode](https://code.visualstudio.com/Download)

## Python 3.11.0
[Python](https://www.python.org/downloads/windows/) is needed in Windows for GitBash and VSCode.

## SSH Key Setup

````bash
ssh-keygen -t ed25519 -C "s0k0j4m3s@gmail.com"
````
````bash
cat ~/.ssh/id_ed25519.pub
````
1. Copy the full output (starts with ssh-ed25519).
2. Go to GitHub → Settings → SSH and GPG keys
3. Click “New SSH key”
4. Paste the public key
5. Give it a title (e.g., "Parrot OS")
6. Click “Add SSH key”

````bash
ssh -T git@github.com
````
````bash
git config --global user.email "s0k0j4m3s@gmail.com"
````
````bash
git config --global user.name "SokoJames"
````

## Initial Repository Setup

````bash
git init
````
````bash
git remote add origin git@github.com:sokonalysis/sokonalysis.git 
````
````bash
git add .
````
````bash
git commit -m "Initial commit — sokonalysis v3.5 GUI"
````
````bash
git branch -M main
````
````bash
git checkout --ours .gitignore
````
````bash
git add .gitignore
````
````bash
git pull origin main --rebase
````
````bash
git push -u origin main
````

## Repository Download 
````bash
git clone git@github.com:sokonalysis/sokonalysis.git
````

## Requirements
### Linux
````bash
python3 -m venv venv
````
````bash
source venv/bin/activate
````
````bash
pip install -r requirements.txt
````

### Windows
````bash
python -m venv venv
````
````bash
source venv/Scripts/activate
````
````bash
pip install -r requirements.txt
````

## File Upload
````bash
git status
````
````bash
git pull origin main
````
````bash
git add .
````
````bash
git commit -m "You comment for a recent update"
````
````bash
git push -u origin main --force
````

If it fails, and requests for your GitHub username and password use
````bash
git remote set-url origin git@github.com:sokonalysis/sokonalysis.git
````

## App Development
### Linux
#### Build
If the sokonalysis_*_all.deb file already exists, you can remove it. For example,

````bash
rm sokonalysis_3.5.0_all.deb
````

else

````bash
./build_deb.sh
````

#### Installation
````bash
dpkg -i sokonalysis_3.5.0_all.deb
````

### Windows
#### Requirements
##### John The Ripper
1. Download it on https://github.com/openwall/john-packages/releases and select winX64_1_JtR.zip
2. Once the downlaod is complete, extract the zip file
3. Press the extracted JtR folder in /sokonalysis-GUI only update it when John releases a new version

#### Build
````bash
./build.bat
````

##### Inno Setup
[Download](https://jrsoftware.org/isinfo.php) and install Inno Setup

**MANUAL INSTRUCTIONS (Two Options)**
1. Open Inno Setup Compiler
2. Open the installer script
3. Click **File** → **Open**
4. Navigate to your project folder (where **build.bat** is)
5. Select **installer.iss**
6. Click **Open**
7. Click **Build** → **Compile** (or press Ctrl+F9)

Wait for compilation to finish. The installer will be in your dist folder .Find the installer at: dist\sokonalysis-3.5.0-windows-installer.exe

## Files To Change When Adding New Components 
### gui/main_window.py
#### Add import
For example
   
````bash
from gui.transposition_railfence import TranspositionRailFencePage
````
#### Add handler in _on_category_option_clicked** 
For example

````bash
elif option_name == "Rail Fence":
   self._show_transposition_railfence()
````

#### Add method
For example
   
````bash
def _show_transposition_railfence(self):
   page_key = "transposition_railfence"
   if page_key not in self.category_pages:
      page = TranspositionRailFencePage(self.theme, lambda: self._show_transposition_page())
      self.category_pages[page_key] = page
      self.stack.addWidget(page)
   self.stack.setCurrentWidget(self.category_pages[page_key])
 ````

#### Wordlist 
For example

````bash
def _on_wordlist_configured(self, wordlist_path, split_parts):
self.shared_wordlist_path = wordlist_path
self.shared_split_parts = split_parts

for key in ["hashing_detail", "md5_page", "sha_page", "wifi_page", "caesar_bruteforce", "crack_zip_page", "crack_rar_page", "crack_7z_page", "steganography_extract"]:
	if key in self.category_pages:
		self.category_pages[key].set_wordlist_config(wordlist_path, split_parts)
````


