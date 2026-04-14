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

echo Configuring LaTeX environment...

:: 2. Check Google connectivity and set proxy
set "USE_PROXY=0"
set "PROXY_URL=http://127.0.0.1:7890"
echo Checking network connectivity...

:: Test Google connectivity (timeout 3 seconds)
curl -s --connect-timeout 3 --max-time 5 -o nul -w "%%{http_code}" https://www.google.com > "%TEMP%\google_test.txt" 2>nul
set /p HTTP_CODE=<"%TEMP%\google_test.txt"
del "%TEMP%\google_test.txt" 2>nul

if "!HTTP_CODE!"=="200" (
    set "USE_PROXY=1"
)

:: Setup curl with proxy if needed
set "CURL_PROXY="
if "!USE_PROXY!"=="1" (
    set "CURL_PROXY=--proxy %PROXY_URL%"
)

:: 3. Download TinyTeX using curl
if not exist "%INSTALL_DIR%" (
    echo Downloading TinyTeX...
    if "!USE_PROXY!"=="1" (
        curl -L %CURL_PROXY% --connect-timeout 30 --retry 3 -o "%ZIP_PATH%" "%ZIP_URL%"
    ) else (
        curl -L --connect-timeout 30 --retry 3 -o "%ZIP_PATH%" "%ZIP_URL%"
    )

    if !errorlevel! neq 0 (
        echo [ERROR] TinyTeX download failed.
        del "%ZIP_PATH%" 2>nul
        pause
        exit /b 1
    )

    echo Extracting TinyTeX...
    if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
    tar -xf "%ZIP_PATH%" -C "%ROOT_DIR%."

    if !errorlevel! equ 0 (
        del "%ZIP_PATH%"
        echo TinyTeX installed successfully.
    ) else (
        echo [ERROR] Extraction failed.
        pause
        exit /b 1
    )
) else (
    echo TinyTeX already exists, skipping download.
)

:: 4. Environment variables and package management
set "PATH=%INSTALL_DIR%\bin\windows;%PATH%"

:: Setup tlmgr proxy if needed
if "!USE_PROXY!"=="1" (
    echo Setting tlmgr proxy: %PROXY_URL%
    call tlmgr option proxy %PROXY_URL%
    call tlmgr option repository https://mirrors.aliyun.com/CTAN/systems/texlive/tlnet/
) else (
    echo Using direct connection for tlmgr.
    call tlmgr option repository https://mirrors.aliyun.com/CTAN/systems/texlive/tlnet/
)

:: Update tlmgr itself first
echo Updating tlmgr...
call tlmgr update --self --no-auto-remove
echo tlmgr update completed.

if exist "%PACKAGE_LIST%" (
    echo Installing packages from list...
    for /f "usebackq tokens=*" %%i in ("%PACKAGE_LIST%") do (
        set "line=%%i"
        set "firstchar=!line:~0,1!"
        if not "!firstchar!"=="#" if not "!line!"=="" (
            echo Installing: !line!
            if "!USE_PROXY!"=="1" (
                call tlmgr install !line! --verify-repo=0
            ) else (
                call tlmgr install !line!
            )
        )
    )
)

echo LaTeX configuration completed
exit /b 0
