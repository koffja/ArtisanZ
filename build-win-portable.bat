@echo off
REM ========================================
REM Artisan Windows Portable Build Script
REM ========================================
REM This script builds a complete portable
REM (green) edition that runs without
REM requiring any dependencies on the
REM target Windows 11 x64 system.
REM ========================================

setlocal enabledelayedexpansion

echo.
echo ========================================
echo Artisan Portable Build Script
echo Target: Windows 11 x64 (Green Edition)
echo ========================================
echo.

REM Change to src directory
cd /d "%~dp0src"
if errorlevel 1 (
    echo ERROR: Cannot find src directory
    pause
    exit /b 1
)

echo [1/6] Checking Python environment...
python --version
if errorlevel 1 (
    echo ERROR: Python not found
    pause
    exit /b 1
)

echo.
echo [2/6] Verifying PyInstaller is installed...
python -c "import PyInstaller; print(f'PyInstaller version: {PyInstaller.__version__}')"
if errorlevel 1 (
    echo ERROR: PyInstaller not found
    echo Installing PyInstaller...
    pip install pyinstaller==6.17.0
)

echo.
echo [3/6] Cleaning previous build...
if exist "dist\artisan" (
    echo Removing old build directory...
    rmdir /s /q "dist\artisan"
)
if exist "build" (
    echo Removing build cache...
    rmdir /s /q "build"
)

echo.
echo [4/6] Starting PyInstaller build...
echo This may take several minutes...
echo.

python -m PyInstaller artisan-win.spec --clean --noconfirm
if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller build failed!
    echo Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo [5/6] Verifying build output...
if not exist "dist\artisan\artisan.exe" (
    echo ERROR: artisan.exe not found in dist\artisan\
    pause
    exit /b 1
)

echo Build artifacts verified:
dir /b "dist\artisan\*.exe"

echo.
echo [6/6] Checking for VC++ Runtime DLLs...
set "vc_missing=0"
for %%f in (msvcp140.dll vcruntime140.dll ucrtbase.dll) do (
    if not exist "dist\artisan\%%f" (
        echo WARNING: %%f not found in build
        set "vc_missing=1"
    ) else (
        echo Found: %%f
    )
)

if "!vc_missing!"=="1" (
    echo.
    echo WARNING: Some VC++ Runtime DLLs are missing.
    echo The application may not run on all systems.
    echo.
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Output directory: %CD%\dist\artisan\
echo.

REM Calculate directory size
for /f "tokens=3" %%a in ('dir /s "dist\artisan" ^| find "File(s)"') do set size=%%a
echo Total size: %size% bytes

echo.
echo To create a portable package:
echo 1. Copy the entire "dist\artisan" folder
echo 2. Paste it on any Windows 11 x64 computer
echo 3. Run artisan.exe directly (no installation needed)
echo.

pause
