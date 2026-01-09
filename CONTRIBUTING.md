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
mkdir -p AppDir/usr/{bin,lib,share/sokonalysis}
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
cp wordlist.txt AppDir/usr/share/sokonalysis/
````

````bash
ldd sokonalysis | grep "=> /" | awk '{print $3}' | xargs -I '{}' cp -v '{}' AppDir/usr/lib/
````

````bash
cat > AppDir/AppRun << 'EOF'
#!/bin/bash
H=$(dirname "$(readlink -f "${0}")")
export PYTHONPATH="$H/usr/share/sokonalysis"
export SOKO_WORDLIST="$H/usr/share/sokonalysis/wordlist.txt"
cd "$(pwd -P)"
exec "$H/usr/bin/sokonalysis" "$@"
EOF
````

````bash
chmod +x AppDir/AppRun
````

````bash
cat > AppDir/sokonalysis.desktop << 'EOF'
[Desktop Entry]
Name=SokoNalysis CLI
Comment=The Cipher Toolkit Built For All Skill Levels
Exec=sokonalysis
Icon=sokonalysis
Type=Application
Categories=Utility;Security;
Terminal=true
EOF
````

````bash
[ -f "../logo.png" ] && cp "../logo.png" AppDir/sokonalysis.png
````

````bash
chmod +x appimagetool-x86_64.AppImage
````

````bash
./appimagetool-x86_64.AppImage AppDir sokonalysis-cli-x86_64.AppImage
````

## Contributors
Thanks to everyone who has contributed!
![Contributors](https://img.shields.io/github/contributors/SokoJames/sokonalysis)
[![](https://contrib.rocks/image?repo=SokoJames/sokonalysis)](https://github.com/SokoJames/sokonalysis/graphs/contributors)
