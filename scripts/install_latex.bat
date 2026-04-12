@echo off
setlocal enabledelayedexpansion

:: 1. Path initialization
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
set "ROOT_DIR=%~dp0..\"
for %%i in ("%ROOT_DIR%") do set "ROOT_DIR=%%~fi"

set "PACKAGE_LIST=%ROOT_DIR%latex_packages.txt"
set "ZIP_URL=https://github.com/rstudio/tinytex-releases/releases/download/v2026.03.02/TinyTeX-v2026.03.02.zip"
set "ZIP_PATH=%ROOT_DIR%TinyTeX.zip"
set "INSTALL_DIR=%ROOT_DIR%TinyTeX"
set "ARIA2_EXE=%ROOT_DIR%aria2c.exe"

echo Configuring LaTeX environment...

:: 2. Check and download aria2c
if not exist "%ARIA2_EXE%" (
    echo Downloading aria2c...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-64bit-build1.zip' -OutFile '%ROOT_DIR%aria2.zip'"

    if not exist "%ROOT_DIR%aria2_temp" mkdir "%ROOT_DIR%aria2_temp"

    tar -xf "%ROOT_DIR%aria2.zip" -C "%ROOT_DIR%aria2_temp"

    for /f "delims=" %%f in ('dir /s /b "%ROOT_DIR%aria2_temp\aria2c.exe"') do (
        move /y "%%f" "%ARIA2_EXE%" >nul
    )

    rd /s /q "%ROOT_DIR%aria2_temp" >nul 2>&1
    del "%ROOT_DIR%aria2.zip" >nul 2>&1
)

:: 3. Download TinyTeX
if not exist "%INSTALL_DIR%" (
    echo Downloading TinyTeX with aria2c...
    "%ARIA2_EXE%" --all-proxy="http://127.0.0.1:7890" -x 16 -s 16 --check-certificate=false -d "%ROOT_DIR%." -o "TinyTeX.zip" "%ZIP_URL%"

    if !errorlevel! neq 0 (
        echo [WARN] aria2c download failed, trying fallback...
        powershell -Command "Invoke-WebRequest -Uri '%ZIP_URL%' -OutFile '%ZIP_PATH%'"
    )

    echo Extracting with tar...
    if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
    tar -xf "%ZIP_PATH%" -C "%ROOT_DIR%."

    if !errorlevel! equ 0 (
        del "%ZIP_PATH%"
    ) else (
        echo [ERROR] Extraction failed.
        pause
        exit /b 1
    )
)

:: 4. Environment variables and package management
set "PATH=%INSTALL_DIR%\bin\windows;%PATH%"

call tlmgr option repository https://mirrors.aliyun.com/CTAN/systems/texlive/tlnet/

if exist "%PACKAGE_LIST%" (
    echo Installing packages from list...
    for /f "usebackq tokens=*" %%i in ("%PACKAGE_LIST%") do (
        set "line=%%i"
        set "firstchar=!line:~0,1!"
        if not "!firstchar!"=="#" if not "!line!"=="" (
            echo Installing: !line!
            call tlmgr install !line!
        )
    )
)

echo LaTeX configuration completed
exit /b 0
