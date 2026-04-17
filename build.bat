@echo off
setlocal enabledelayedexpansion

echo ================================
echo  PortableLLM - Build Script
echo ================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.10+ first.
    pause
    exit /b 1
)

:: Step 1: Install PyInstaller
echo [1/4] Installing PyInstaller...
pip install PyInstaller >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip install failed.
    pause
    exit /b 1
)
echo Done.
echo.

:: Step 2: Download llama.cpp (CPU, Windows x64) if not present
if not exist "bin\llama-cli.exe" (
    echo [2/4] Downloading llama.cpp...
    curl -sL "https://github.com/ggml-org/llama.cpp/releases/latest/download/llama-b8815-bin-win-cpu-x64.zip" -o llama-cpu.zip
    if not exist "llama-cpu.zip" (
        echo ERROR: Download failed.
        pause
        exit /b 1
    )
    echo Extracting...
    python -c "import zipfile,os,shutil; z=zipfile.ZipFile('llama-cpu.zip'); os.makedirs('bin',exist_ok=True); [z.extract(f,'bin') for f in z.namelist() if f.endswith(('.exe','.dll'))]; z.close(); os.remove('llama-cpu.zip'); [shutil.move(os.path.join('bin',n),os.path.join('bin',n.split('/')[-1])) for n in z.namelist()]" 2>nul
    echo Done.
) else (
    echo [2/4] llama.cpp already present in bin/
)
echo.

:: Step 3: Build executable (minimal dependencies + llama-server)
echo [3/4] Building PortableLLM.exe...
pyinstaller --onedir --name PortableLLM ^
    --add-data "bin\llama-server.exe;." ^
    --add-data "bin\llama.dll;." ^
    --add-data "bin\ggml.dll;." ^
    --add-data "bin\ggml-base.dll;." ^
    --add-data "bin\ggml-cpu-x64.dll;." ^
    --add-data "bin\ggml-cpu-sse42.dll;." ^
    --add-data "bin\ggml-cpu-haswell.dll;." ^
    --add-data "bin\ggml-cpu-alderlake.dll;." ^
    --add-data "bin\ggml-cpu-zen4.dll;." ^
    --add-data "bin\ggml-cpu-sapphirerapids.dll;." ^
    --add-data "bin\libomp140.x86_64.dll;." ^
    --exclude-module ssl ^
    --exclude-module _ssl ^
    --exclude-module _hashlib ^
    --exclude-module _bz2 ^
    --exclude-module _lzma ^
    --exclude-module _decimal ^
    --exclude-module tkinter ^
    --exclude-module unittest ^
    --exclude-module doctest ^
    --exclude-module pdb ^
    --exclude-module pydoc ^
    --exclude-module xml ^
    --exclude-module html ^
    --exclude-module sqlite3 ^
    --exclude-module multiprocessing ^
    --exclude-module concurrent ^
    --exclude-module ctypes ^
    --exclude-module logging ^
    --strip ^
    --clean ^
    --noconfirm ^
    scripts\chat.py

:: Clean up unnecessary files after build
echo Cleaning up unnecessary files...
cd dist\PortableLLM\_internal
del /q _bz2.pyd _lzma.pyd _decimal.pyd LIBBZ2.dll liblzma.dll 2>nul
cd ..\..\..

if errorlevel 1 (
    echo ERROR: PyInstaller build failed.
    pause
    exit /b 1
)
echo.

:: Step 4: Create models and kb folders in dist
echo [4/4] Setting up folders...
if not exist "dist\PortableLLM\models" mkdir dist\PortableLLM\models
if not exist "dist\PortableLLM\kb" mkdir dist\PortableLLM\kb
if exist "kb" xcopy /q /y "kb\*" "dist\PortableLLM\kb\"
if exist "config.json" copy /y "config.json" "dist\PortableLLM\"

echo.
echo ========================================
echo  Build complete!
echo  Output: dist\PortableLLM\
echo ========================================
echo.
echo  To use on any computer:
echo    1. Copy dist\PortableLLM\ folder to USB drive
echo    2. Place .gguf model files in models\
echo    3. Place .txt/.md knowledge files in kb\
echo    4. Double-click PortableLLM.exe
echo.
echo  Configure: config.json
echo  KB commands: /kb list, /kb on/off ^<file^>, /kb all, /kb none
echo ========================================
echo.
pause
