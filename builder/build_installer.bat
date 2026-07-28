@echo off
:: ==============================================================================
:: 🌸 SANYYY WINDOWS INSTALLER 1-CLICK BUILD SCRIPT (.bat)
:: ==============================================================================
:: This script compiles Sanyyy into Sanyyy.exe and generates SanyyySetup.exe
:: Run this file on a Windows Machine or VM!
:: ==============================================================================

echo [1/3] Installing Required Python Build Dependencies...
pip install pyinstaller google-genai pyaudio sounddevice requests pillow

echo.
echo [2/3] Building Sanyyy.exe with PyInstaller...
python builder/build_windows_exe.py

echo.
echo [3/3] Compiling SanyyySetup.exe Installer via Inno Setup...
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" builder/inno_setup_script.iss
    echo.
    echo 🎉 SUCCESS! Your Windows Installer is ready under:
    echo 📁 sanyyyPackage\output\SanyyySetup.exe
) else (
    echo.
    echo ⚠️ Inno Setup 6 compiler (ISCC.exe) was not found in default directory.
    echo You can open inno_setup_script.iss in Inno Setup GUI to compile SanyyySetup.exe!
    echo Or grab your compiled folder at: sanyyyPackage\dist\Sanyyy\Sanyyy.exe
)

pause
