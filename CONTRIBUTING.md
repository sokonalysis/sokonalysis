# Developers Only
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

## Building a Standalone Application 
````bash
wget -c https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
````

````bash
mkdir -p AppDir/usr/{bin,lib}
````

````bash
cp sokonalysis AppDir/usr/bin/
````

````bash
cp *.py AppDir/usr/share/sokonalysis/
````

````bash
rm -f AppDir/usr/share/sokonalysis/sokonalysis_gui.py 2>/dev/null || true
````
````bash
if [ -d "pythonvenv" ]; then
    cp -r pythonvenv/lib/python3.*/site-packages/* AppDir/usr/share/sokonalysis/
else
    echo "Creating temporary Python environment..."
    python3 -m venv /tmp/soko_temp
    source /tmp/soko_temp/bin/activate
    pip install -r requirements.txt
    cp -r /tmp/soko_temp/lib/python3.*/site-packages/* AppDir/usr/share/sokonalysis/
    deactivate
fi
````

````bash
cp *.cpp *.h AppDir/usr/share/sokonalysis/ 2>/dev/null || true
````

````bash
cp wordlist.txt AppDir/usr/share/sokonalysis/ 2>/dev/null || mkdir -p AppDir/usr/share/sokonalysis && cp wordlist.txt AppDir/usr/share/sokonalysis/
````

````bash
ldd sokonalysis | grep "=> /" | awk '{print $3}' | xargs -I '{}' cp -v '{}' AppDir/usr/lib/
````

````bash
if [ -d "pythonvenv" ]; then
    cp -r pythonvenv/lib/python3.*/site-packages/* AppDir/usr/share/sokonalysis/
else
    echo "Creating temporary Python environment..."
    python3 -m venv /tmp/soko_temp
    source /tmp/soko_temp/bin/activate
    pip install -r requirements.txt
    cp -r /tmp/soko_temp/lib/python3.*/site-packages/* AppDir/usr/share/sokonalysis/
    deactivate
fi

# 4. Copy wordlist
cp wordlist.txt AppDir/usr/share/sokonalysis/

# 5. Copy shared libraries
ldd sokonalysis | grep "=> /" | awk '{print $3}' | xargs -I '{}' cp -v '{}' AppDir/usr/lib/

# 6. FIXED AppRun for CLI with Python support
cat > AppDir/AppRun << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"

# Essential environment for C++ binary
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"

# CRITICAL: Python environment for scripts called by CLI
export PYTHONPATH="${HERE}/usr/share/sokonalysis:${PYTHONPATH}"
export PATH="${HERE}/usr/share/sokonalysis:${PATH}"

# Wordlist path for C++ binary
export SOKO_WORDLIST="${HERE}/usr/share/sokonalysis/wordlist.txt"

# Change to script directory (Python scripts might expect this)
cd "${HERE}/usr/share/sokonalysis"

# Always run CLI version (no GUI option)
exec "${HERE}/usr/bin/sokonalysis" "$@"
EOF
````

````bash
chmod +x AppDir/AppRun
````

````bash
cat > AppDir/sokonalysis.desktop << 'EOF'
[Desktop Entry]
Name=sokoNalysis CLI
Comment=The Cipher Toolkit Built For All Skill Levels
Exec=sokonalysis
Icon=sokonalysis
Type=Application
Categories=Utility;Security;ConsoleOnly;
Terminal=true
EOF
````

````bash
[ -f "../logo.png" ] && cp "../logo.png" AppDir/sokonalysis.png
````

````bash
./appimagetool-x86_64.AppImage AppDir sokonalysis-cli-x86_64.AppImage
````

## Contributors
Thanks to everyone who has contributed!
![Contributors](https://img.shields.io/github/contributors/SokoJames/sokonalysis)
[![](https://contrib.rocks/image?repo=SokoJames/sokonalysis)](https://github.com/SokoJames/sokonalysis/graphs/contributors)
