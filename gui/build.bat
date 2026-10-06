@echo off
REM build.bat - Build standalone sokonalysis application for Windows

set APP_NAME=sokonalysis
set VERSION=3.5.0
set BUILD_DIR=dist
set PACKAGE_DIR=%BUILD_DIR%\%APP_NAME%-%VERSION%
set JTR_DIR=JtR

echo =========================================
echo   Building %APP_NAME% v%VERSION% for Windows
echo =========================================
echo.

echo [1/7] Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist %PACKAGE_DIR% rmdir /s /q %PACKAGE_DIR%
for %%f in (*.spec) do del /q "%%f"

echo [2/7] Installing build dependencies...
pip install --upgrade pip
pip install pyinstaller PySide6 matplotlib pycryptodome distro requests

echo [3/7] Verifying John the Ripper...
if not exist "%JTR_DIR%\run\john.exe" (
    echo ERROR: John the Ripper not found at %JTR_DIR%\run\john.exe!
    echo Please place the JtR folder with john.exe in the project root.
    echo Download from: https://github.com/openwall/john-packages/releases
    echo Extract and rename the folder to 'JtR'
    pause
    exit /b 1
)

REM Verify john works
"%JTR_DIR%\run\john.exe" >nul 2>&1
if %ERRORLEVEL% LEQ 1 (
    echo John the Ripper verified successfully!
    "%JTR_DIR%\run\john.exe" --version 2>&1 | findstr /i "john"
) else (
    echo WARNING: John the Ripper may not work correctly
)

REM Verify all john tools exist
for %%t in (zip2john.exe rar2john.exe pdf2john.exe office2john.exe hccap2john.exe) do (
    if exist "%JTR_DIR%\run\%%t" (
        echo   ✓ %%t found
    ) else (
        echo   ✗ %%t missing - some cracking features will be unavailable
    )
)

echo [4/7] Verifying assets...
set ICON_COUNT=0
if exist "assets\icons" (
    for %%f in (assets\icons\*.png) do set /a ICON_COUNT+=1
    echo   ✓ Toolbar icons: %ICON_COUNT% images
)

REM Verify guide PDF
if exist "assets\docs\guide.pdf" (
    echo   ✓ Guide PDF found
) else if exist "assets\guide.pdf" (
    echo   ✓ Guide PDF found (in assets/)
) else (
    echo   ⚠ No guide PDF found
)

REM Verify Morse symbols
set MORSE_COUNT=0
if exist "assets\symbols\morse" (
    for %%f in (assets\symbols\morse\*.png) do set /a MORSE_COUNT+=1
    echo   ✓ Morse symbols: !MORSE_COUNT! images
) else (
    echo   ⚠ No Morse symbols found
)

REM Verify Pigpen symbols
set PIGPEN_COUNT=0
if exist "assets\symbols\pigpen" (
    for %%f in (assets\symbols\pigpen\*.png) do set /a PIGPEN_COUNT+=1
    echo   ✓ Pigpen symbols: !PIGPEN_COUNT! images
) else (
    echo   ⚠ No Pigpen symbols found
)

REM Verify Navy symbols
set NAVY_COUNT=0
if exist "assets\symbols\navy" (
    for %%f in (assets\symbols\navy\*.png) do set /a NAVY_COUNT+=1
    echo   ✓ Navy signal symbols: !NAVY_COUNT! images
) else (
    echo   ⚠ No Navy signal symbols found
)

echo [5/7] Building GUI executable...
pyinstaller ^
    --name="%APP_NAME%" ^
    --windowed ^
    --onefile ^
    --add-data="assets;assets" ^
    --add-data="version.txt;." ^
    --add-data="LICENSE;." ^
    --add-data="EN.json;." ^
    --add-data="%JTR_DIR%;JtR" ^
    --icon="assets/logo.png" ^
    --hidden-import=PySide6 ^
    --hidden-import=PySide6.QtCore ^
    --hidden-import=PySide6.QtGui ^
    --hidden-import=PySide6.QtWidgets ^
    --hidden-import=matplotlib ^
    --hidden-import=matplotlib.backends.backend_qt5agg ^
    --hidden-import=Crypto ^
    --hidden-import=distro ^
    --hidden-import=requests ^
    --collect-all=PySide6 ^
    main.py

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: GUI build failed!
    pause
    exit /b 1
)

echo [6/7] Creating release package...
mkdir "%PACKAGE_DIR%" 2>nul
mkdir "%PACKAGE_DIR%\assets" 2>nul
mkdir "%PACKAGE_DIR%\assets\icons" 2>nul
mkdir "%PACKAGE_DIR%\assets\symbols" 2>nul
mkdir "%PACKAGE_DIR%\assets\symbols\morse" 2>nul
mkdir "%PACKAGE_DIR%\assets\symbols\pigpen" 2>nul
mkdir "%PACKAGE_DIR%\assets\symbols\navy" 2>nul
mkdir "%PACKAGE_DIR%\assets\docs" 2>nul

REM Copy executables
copy /Y "dist\%APP_NAME%.exe" "%PACKAGE_DIR%\"

REM Copy assets and documentation
xcopy /E /I /Y "assets\icons" "%PACKAGE_DIR%\assets\icons"
xcopy /E /I /Y "assets\symbols\morse" "%PACKAGE_DIR%\assets\symbols\morse" 2>nul
xcopy /E /I /Y "assets\symbols\pigpen" "%PACKAGE_DIR%\assets\symbols\pigpen" 2>nul
xcopy /E /I /Y "assets\symbols\navy" "%PACKAGE_DIR%\assets\symbols\navy" 2>nul
if exist "assets\docs\guide.pdf" copy /Y "assets\docs\guide.pdf" "%PACKAGE_DIR%\assets\docs\" 2>nul
if exist "assets\guide.pdf" copy /Y "assets\guide.pdf" "%PACKAGE_DIR%\assets\" 2>nul
copy /Y "version.txt" "%PACKAGE_DIR%\"
copy /Y "README.md" "%PACKAGE_DIR%\" 2>nul
copy /Y "LICENSE" "%PACKAGE_DIR%\" 2>nul
copy /Y "CHANGELOG.md" "%PACKAGE_DIR%\" 2>nul
copy /Y "EN.json" "%PACKAGE_DIR%\" 2>nul

REM Create README for Windows users
(
echo sokonalysis v%VERSION% - Windows Portable
echo ==========================================
echo.
echo Quick Start:
echo   1. Double-click "sokonalysis.exe"
echo.
echo Requirements:
echo   - Windows 10 or later (64-bit)
echo   - No Python installation required
echo.
echo Features:
echo   - Hash Cracking (MD5, SHA1, SHA256, SHA512)
echo   - Password Cracking (ZIP, RAR, PDF, Office)
echo   - Wi-Fi Handshake Cracking
echo   - Linux passwd/shadow Cracking
echo   - Caesar Ciphers (Basic, Poly, Brute Force)
echo   - RSA, Diffie-Hellman, MITM Attacks
echo   - Steganography (Embed/Extract)
echo   - Base Encoding (2-100)
echo   - Morse Code, Pigpen, Navy Signals, Substitution Ciphers
echo   - File Integrity Verification
echo   - Online Hash Lookup
echo   - Cipher Identifier
echo.
echo Included Tools:
echo   - John the Ripper (john, zip2john, rar2john, pdf2john, office2john)
echo   - Python runtime (bundled)
echo.
echo For updates and documentation, visit the repository.
) > "%PACKAGE_DIR%\README.txt"

echo [7/7] Creating archive...
powershell Compress-Archive -Path "%PACKAGE_DIR%" -DestinationPath "%BUILD_DIR%\%APP_NAME%-%VERSION%-windows-portable.zip" -Force

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Archive creation failed!
    pause
    exit /b 1
)

REM Create SHA256 checksum
powershell Get-FileHash "%BUILD_DIR%\%APP_NAME%-%VERSION%-windows-portable.zip" -Algorithm SHA256 ^> "%BUILD_DIR%\%APP_NAME%-%VERSION%-windows-portable.zip.sha256"

REM Display file size
for %%A in ("%BUILD_DIR%\%APP_NAME%-%VERSION%-windows-portable.zip") do (
    set SIZE=%%~zA
    set /a SIZE_MB=%%~zA/1048576
    echo   Archive size: !SIZE_MB! MB
)

echo.
echo =========================================
echo   Portable build complete!
echo   Output: %BUILD_DIR%\%APP_NAME%-%VERSION%-windows-portable.zip
echo.
echo   Package contains:
echo   - sokonalysis.exe (GUI)
echo   - JtR/ (John the Ripper + all tools)
echo   - assets/icons/ (!ICON_COUNT! toolbar icons)
echo   - assets/symbols/ (Morse: !MORSE_COUNT!, Pigpen: !PIGPEN_COUNT!, Navy: !NAVY_COUNT!)
echo   - assets/docs/guide.pdf
echo   - version.txt
echo   - LICENSE
echo   - README.txt
echo =========================================
echo.
echo =========================================
echo   CREATE WINDOWS INSTALLER MANUALLY
echo =========================================
echo.
echo To create the installer EXE:
echo.
echo   OPTION 1 - GUI:
echo     1. Open "Inno Setup Compiler" from Start Menu
echo     2. File ^> Open ^> select "installer.iss"
echo     3. Build ^> Compile (Ctrl+F9)
echo.
echo   OPTION 2 - Command Line:
echo     "C:\Program Files\Inno Setup 7\ISCC.exe" installer.iss
echo.
echo   The installer will be created as:
echo     dist\%APP_NAME%-%VERSION%-windows-installer.exe
echo =========================================
pause