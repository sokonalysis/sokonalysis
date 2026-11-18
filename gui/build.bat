@echo off
setlocal enableextensions

REM ---------------------------------------------------------------
REM sokonalysis build script for Windows (PyInstaller portable zip)
REM Run this from the gui\ folder, inside the build venv.
REM
REM Optional environment variables:
REM   PYTHON=python        Python interpreter to use (default: python)
REM                        (use a path without spaces, e.g. py -3.12 is NOT supported)
REM   KEEP_BUILD=1         Keep build\ and *.spec after the build (debugging)
REM   NO_PAUSE=1           Do not pause at the end (CI use)
REM   ISCC=path\ISCC.exe   Inno Setup compiler (auto-detected if not set)
REM ---------------------------------------------------------------

if "%PYTHON%"=="" set PYTHON=python
set APP_NAME=sokonalysis
set BUILD_DIR=dist
set JTR_DIR=JtR

REM ---- Read version from version.txt (never hardcoded) ----
if not exist "version.txt" (
    echo ERROR: version.txt not found.
    goto :fail
)
set /p VERSION=<version.txt
set VERSION=%VERSION: =%
if "%VERSION%"=="" (
    echo ERROR: version.txt is empty.
    goto :fail
)

set PACKAGE_DIR=%BUILD_DIR%\%APP_NAME%-%VERSION%
set ZIP_NAME=%APP_NAME%-%VERSION%-windows-portable.zip
set ZIP_PATH=%BUILD_DIR%\%ZIP_NAME%

echo =========================================
echo   Building %APP_NAME% v%VERSION% for Windows
echo =========================================
echo.

REM ---- Python checks ----
for /f %%v in ('%PYTHON% -c "import sys; print(sys.version_info.major, sys.version_info.minor, sep=chr(46))"') do set PYVER=%%v
if "%PYVER%"=="" (
    echo ERROR: Could not run Python interpreter "%PYTHON%".
    goto :fail
)
echo Using Python %PYVER%
for %%p in (3.13 3.14 3.15) do if "%PYVER%"=="%%p" echo   [WARN] Python %PYVER% is very new. Python 3.12 is the safest choice for PyInstaller builds.

echo [1/7] Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
for %%f in (*.spec) do del /q "%%f"

echo [2/7] Installing build dependencies...
"%PYTHON%" -m pip install --upgrade pip
if exist requirements.txt (
    echo   Using requirements.txt
    "%PYTHON%" -m pip install -r requirements.txt
)
"%PYTHON%" -m pip install --upgrade pyinstaller PySide6 matplotlib pycryptodome distro requests pymupdf
if errorlevel 1 (
    echo ERROR: Dependency installation failed.
    goto :fail
)
"%PYTHON%" -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: PyInstaller is not available for %PYTHON%.
    goto :fail
)

echo [3/7] Verifying John the Ripper...
if not exist "%JTR_DIR%\run\john.exe" (
    echo ERROR: John the Ripper not found at %JTR_DIR%\run\john.exe
    echo Place the JtR folder with john.exe in the project root.
    echo Download from: https://github.com/openwall/john-packages/releases
    echo Extract and rename the folder to JtR
    goto :fail
)
"%JTR_DIR%\run\john.exe" >nul 2>&1
if %ERRORLEVEL% LEQ 1 (
    echo   [OK] John the Ripper verified
) else (
    echo   [WARN] John the Ripper may not work correctly
)
for %%t in (zip2john.exe rar2john.exe pdf2john.exe office2john.exe hccap2john.exe) do call :check_tool %%t

echo [4/7] Verifying assets and data files...
call :count "assets\icons" ICON_COUNT
call :count "assets\symbols\morse" MORSE_COUNT
call :count "assets\symbols\pigpen" PIGPEN_COUNT
call :count "assets\symbols\navy" NAVY_COUNT
echo   Toolbar icons: %ICON_COUNT% images
echo   Morse symbols: %MORSE_COUNT% images
echo   Pigpen symbols: %PIGPEN_COUNT% images
echo   Navy signal symbols: %NAVY_COUNT% images

set GUIDE_SRC=
if exist "assets\docs\guide.pdf" set GUIDE_SRC=assets\docs\guide.pdf
if "%GUIDE_SRC%"=="" if exist "assets\guide.pdf" set GUIDE_SRC=assets\guide.pdf
if "%GUIDE_SRC%"=="" (
    echo   [WARN] No guide.pdf found - user guide will show not found
) else (
    echo   [OK] Guide PDF: %GUIDE_SRC%
)

if not exist gui mkdir gui
if exist "gui\ai_operations.json" (
    echo   [OK] ai_operations.json found
) else (
    echo   [WARN] ai_operations.json not found - creating empty file
    echo {"operations": {}, "file_handlers": {}}>gui\ai_operations.json
)
if exist "gui\english_words.json" (
    echo   [OK] english_words.json found
) else (
    echo   [WARN] english_words.json not found - creating empty file
    echo []>gui\english_words.json
)

echo [5/7] Building GUI executable...

REM Icon: prefer .ico, fall back to .png
set ICON_FILE=assets\logo.png
if exist "assets\logo.ico" set ICON_FILE=assets\logo.ico

set PYI_ARGS=--clean --onefile --noconsole --name %APP_NAME%
set PYI_ARGS=%PYI_ARGS% --icon "%ICON_FILE%"
set PYI_ARGS=%PYI_ARGS% --add-data "assets;assets"
set PYI_ARGS=%PYI_ARGS% --add-data "version.txt;."
set PYI_ARGS=%PYI_ARGS% --add-data "LICENSE;."
set PYI_ARGS=%PYI_ARGS% --add-data "EN.json;."
set PYI_ARGS=%PYI_ARGS% --add-data "assets\symbols;assets/symbols"
set PYI_ARGS=%PYI_ARGS% --add-data "gui\ai_operations.json;gui"
set PYI_ARGS=%PYI_ARGS% --add-data "gui\english_words.json;gui"
set PYI_ARGS=%PYI_ARGS% --add-data "%JTR_DIR%;JtR"
if not "%GUIDE_SRC%"=="" (
    if "%GUIDE_SRC%"=="assets\docs\guide.pdf" (
        set PYI_ARGS=%PYI_ARGS% --add-data "assets\docs\guide.pdf;assets/docs"
    ) else (
        set PYI_ARGS=%PYI_ARGS% --add-data "assets\guide.pdf;assets"
    )
)
if exist "gui\ai" (
    set PYI_ARGS=%PYI_ARGS% --add-data "gui\ai;gui/ai"
    echo   [OK] gui\ai data files found
)

REM PyMuPDF fix: newer PyMuPDF loads ONNX model/yaml files at import time
REM (pymupdf.layout). --collect-all bundles code, data files and binaries.
call :collect pymupdf
call :collect pymupdf_layout
call :collect onnxruntime

set PYI_ARGS=%PYI_ARGS% --collect-all PySide6
set PYI_ARGS=%PYI_ARGS% --hidden-import fitz
set PYI_ARGS=%PYI_ARGS% --hidden-import PySide6.QtCore
set PYI_ARGS=%PYI_ARGS% --hidden-import PySide6.QtGui
set PYI_ARGS=%PYI_ARGS% --hidden-import PySide6.QtWidgets
set PYI_ARGS=%PYI_ARGS% --hidden-import matplotlib
set PYI_ARGS=%PYI_ARGS% --hidden-import matplotlib.backends.backend_qt5agg
set PYI_ARGS=%PYI_ARGS% --hidden-import matplotlib.backends.backend_qtagg
set PYI_ARGS=%PYI_ARGS% --hidden-import Crypto
set PYI_ARGS=%PYI_ARGS% --hidden-import distro
set PYI_ARGS=%PYI_ARGS% --hidden-import requests

"%PYTHON%" -m PyInstaller %PYI_ARGS% main.py
if errorlevel 1 (
    echo ERROR: GUI build failed.
    goto :fail
)
if not exist "dist\%APP_NAME%.exe" (
    echo ERROR: dist\%APP_NAME%.exe not found after build.
    goto :fail
)

echo [6/7] Creating release package...
mkdir "%PACKAGE_DIR%" 2>nul
mkdir "%PACKAGE_DIR%\assets\docs" 2>nul

copy /Y "dist\%APP_NAME%.exe" "%PACKAGE_DIR%\" >nul

xcopy /E /I /Y "assets" "%PACKAGE_DIR%\assets" >nul 2>&1
copy /Y "version.txt" "%PACKAGE_DIR%\" >nul 2>&1
copy /Y "LICENSE" "%PACKAGE_DIR%\" >nul 2>&1
copy /Y "EN.json" "%PACKAGE_DIR%\" >nul 2>&1
copy /Y "README.md" "%PACKAGE_DIR%\" >nul 2>&1
copy /Y "CHANGELOG.md" "%PACKAGE_DIR%\" >nul 2>&1

mkdir "%PACKAGE_DIR%\gui" 2>nul
copy /Y "gui\ai_operations.json" "%PACKAGE_DIR%\gui\" >nul 2>&1
copy /Y "gui\english_words.json" "%PACKAGE_DIR%\gui\" >nul 2>&1
if exist "gui\ai" xcopy /E /I /Y "gui\ai" "%PACKAGE_DIR%\gui\ai" >nul 2>&1

REM README for Windows users (version comes from version.txt)
set README=%PACKAGE_DIR%\README.txt
echo %APP_NAME% v%VERSION% - Windows Portable>"%README%"
echo ==========================================>>"%README%"
echo.>>"%README%"
echo Quick Start:>>"%README%"
echo   1. Double-click "%APP_NAME%.exe">>"%README%"
echo.>>"%README%"
echo Requirements:>>"%README%"
echo   - Windows 10 or later (64-bit)>>"%README%"
echo   - No Python installation required>>"%README%"
echo.>>"%README%"
echo Features:>>"%README%"
echo   - Hash Cracking (MD5, SHA1, SHA256, SHA512)>>"%README%"
echo   - Password Cracking (ZIP, RAR, PDF, Office)>>"%README%"
echo   - Wi-Fi Handshake Cracking>>"%README%"
echo   - Linux passwd/shadow Cracking>>"%README%"
echo   - Caesar Ciphers (Basic, Poly, Brute Force)>>"%README%"
echo   - RSA, Diffie-Hellman, MITM Attacks>>"%README%"
echo   - Steganography (Embed/Extract)>>"%README%"
echo   - Base Encoding (2-100)>>"%README%"
echo   - Morse Code, Pigpen, Navy Signals, Substitution Ciphers>>"%README%"
echo   - File Integrity Verification>>"%README%"
echo   - Online Hash Lookup>>"%README%"
echo   - Cipher Identifier>>"%README%"
echo.>>"%README%"
echo Bundled Tools:>>"%README%"
echo   - John the Ripper (john, zip2john, rar2john, pdf2john, office2john)>>"%README%"
echo   - Python runtime>>"%README%"
echo.>>"%README%"
echo For updates and documentation, visit the repository.>>"%README%"

echo [7/7] Creating archive...
powershell -NoProfile -Command "Compress-Archive -Path '%PACKAGE_DIR%' -DestinationPath '%ZIP_PATH%' -Force"
if errorlevel 1 (
    echo ERROR: Archive creation failed.
    goto :fail
)

REM SHA256 checksum (standard "hash  filename" format)
powershell -NoProfile -Command "(Get-FileHash '%ZIP_PATH%' -Algorithm SHA256).Hash.ToLower() + '  %ZIP_NAME%'" > "%ZIP_PATH%.sha256"

for %%A in ("%ZIP_PATH%") do set /a SIZE_MB=%%~zA/1048576
echo   Archive size: %SIZE_MB% MB

REM ---- Optional: build installer automatically if Inno Setup is found ----
call :find_iscc
set INSTALLER_BUILT=0
if not "%ISCC%"=="" if exist "installer.iss" (
    echo.
    echo Building installer with Inno Setup...
    "%ISCC%" /DAppName=%APP_NAME% /DAppVersion=%VERSION% installer.iss
    if not errorlevel 1 set INSTALLER_BUILT=1
)

REM ---- Cleanup (dist\ is kept so you can test dist\%APP_NAME%.exe directly) ----
if not "%KEEP_BUILD%"=="1" (
    if exist build rmdir /s /q build
    for %%f in (*.spec) do del /q "%%f"
)

echo.
echo =========================================
echo   Portable build complete
echo   Output: %ZIP_PATH%
echo.
echo   Package contains:
echo   - %APP_NAME%.exe (GUI, John the Ripper embedded)
echo   - assets\icons (%ICON_COUNT% toolbar icons)
echo   - assets\symbols (Morse: %MORSE_COUNT%, Pigpen: %PIGPEN_COUNT%, Navy: %NAVY_COUNT%)
echo   - assets\docs\guide.pdf
echo   - gui\ai_operations.json, gui\english_words.json
echo   - version.txt, LICENSE, README.txt
echo =========================================
echo.
echo Test the raw binary first: dist\%APP_NAME%.exe

if "%INSTALLER_BUILT%"=="1" (
    echo Installer: %BUILD_DIR%\%APP_NAME%-%VERSION%-windows-installer.exe
) else (
    echo.
    echo To create the installer EXE manually:
    echo   GUI: open installer.iss in Inno Setup Compiler, Build ^> Compile
    echo   CLI: ISCC.exe /DAppName=%APP_NAME% /DAppVersion=%VERSION% installer.iss
    echo   Expected output: %BUILD_DIR%\%APP_NAME%-%VERSION%-windows-installer.exe
)
echo.
if not "%NO_PAUSE%"=="1" pause
endlocal
exit /b 0

:fail
echo.
echo Build failed.
if not "%NO_PAUSE%"=="1" pause
endlocal
exit /b 1

REM ================= Subroutines =================

:count
REM %1 = directory, %2 = variable receiving the .png count
set %2=0
if exist "%~1" for %%f in ("%~1\*.png") do set /a %2+=1
exit /b 0

:check_tool
REM %1 = tool name with .exe; newer JtR builds ship some helpers as .py or .pl scripts
if exist "%JTR_DIR%\run\%~n1.exe" (
    echo   [OK] %~n1.exe found
    exit /b 0
)
if exist "%JTR_DIR%\run\%~n1.py" (
    echo   [OK] %~n1.py found ^(script version^)
    exit /b 0
)
if exist "%JTR_DIR%\run\%~n1.pl" (
    echo   [OK] %~n1.pl found ^(script version^)
    exit /b 0
)
echo   [MISSING] %~n1 - some cracking features will be unavailable
exit /b 0

:collect
REM Add --collect-all for a module only if it is installed
"%PYTHON%" -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('%~1') else 1)" >nul 2>&1
if errorlevel 1 exit /b 0
set PYI_ARGS=%PYI_ARGS% --collect-all %~1
echo   [OK] Collecting all files for: %~1
exit /b 0

:find_iscc
if not "%ISCC%"=="" exit /b 0
if exist "%ProgramFiles%\Inno Setup 7\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 7\ISCC.exe"
if "%ISCC%"=="" if exist "%ProgramFiles(x86)%\Inno Setup 7\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 7\ISCC.exe"
if "%ISCC%"=="" if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if "%ISCC%"=="" if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
exit /b 0