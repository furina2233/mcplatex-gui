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

echo [INFO] Configuring LaTeX environment...

:: Check Google connectivity through proxy and decide download mode
set "USE_PROXY=0"
set "PROXY_URL=http://127.0.0.1:7890"
echo [INFO] Checking network connectivity...

:: Added -k to bypass SSL issues common with proxies
curl -s -k -L --connect-timeout 5 --proxy %PROXY_URL% https://www.google.com >nul 2>nul
if !errorlevel! equ 0 (
    echo [INFO] Proxy connection successful
    set "USE_PROXY=1"
    :: Set environment variables for sub-processes
    set "HTTP_PROXY=%PROXY_URL%"
    set "HTTPS_PROXY=%PROXY_URL%"
) else (
    echo [WARN] Proxy connection failed
    set "USE_PROXY=0"
    set "HTTP_PROXY="
    set "HTTPS_PROXY="
)

:: Setup curl with proxy if needed (Added -k)
set "CURL_PROXY="
if "!USE_PROXY!"=="1" (
    set "CURL_PROXY=--proxy %PROXY_URL% -k"
)

:: Download TinyTeX using curl
if not exist "%INSTALL_DIR%" (
    echo [INFO] Downloading TinyTeX...
    curl -L !CURL_PROXY! -k --connect-timeout 30 --retry 3 -o "%ZIP_PATH%" "%ZIP_URL%"

    if !errorlevel! neq 0 (
        echo [ERROR] TinyTeX download failed.
        del "%ZIP_PATH%" 2>nul
        pause
        exit /b 1
    )

    echo [INFO] Extracting TinyTeX...
    if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
    tar -xf "%ZIP_PATH%" -C "%ROOT_DIR%."

    if !errorlevel! equ 0 (
        del "%ZIP_PATH%"
        echo [SUCCESS] TinyTeX installed successfully.
    ) else (
        echo [ERROR] Extraction failed.
        pause
        exit /b 1
    )
) else (
    echo [INFO] TinyTeX already exists, skipping download.
)

:: Environment variables and package management
set "PATH=%INSTALL_DIR%\bin\windows;%PATH%"

:: Setup tlmgr proxy and repository
if "!USE_PROXY!"=="1" (
    echo [INFO] Setting tlmgr proxy: %PROXY_URL%
    call tlmgr option proxy %PROXY_URL%
    :: Using proxy, default repo is usually fine, but mirror is kept for stability
    call tlmgr option repository https://mirrors.aliyun.com/CTAN/systems/texlive/tlnet/
) else (
    echo [INFO] Using direct connection for tlmgr.
    call tlmgr option repository https://mirrors.aliyun.com/CTAN/systems/texlive/tlnet/
)

:: Update tlmgr itself first
echo [INFO] Updating tlmgr...
call tlmgr update --self --no-auto-remove
echo [INFO] tlmgr update completed.

if exist "%PACKAGE_LIST%" (
    echo [INFO] Installing packages from list...
    for /f "usebackq tokens=*" %%i in ("%PACKAGE_LIST%") do (
        set "line=%%i"
        set "firstchar=!line:~0,1!"
        if not "!firstchar!"=="#" if not "!line!"=="" (
            echo Installing: !line!
            if "!USE_PROXY!"=="1" (
                :: Added --verify-repo=0 to avoid SSL issues with proxy
                call tlmgr install !line! --verify-repo=0
            ) else (
                call tlmgr install !line!
            )
        )
    )
)

echo [SUCCESS] LaTeX configuration completed.
exit /b 0