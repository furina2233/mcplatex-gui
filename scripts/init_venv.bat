@echo off
setlocal enabledelayedexpansion

set "BASE_DIR=%~dp0..\"
set "VENV_DIR=%BASE_DIR%\.venv"
set "VENV_ACTIVATE=%VENV_DIR%\Scripts\activate.bat"
set "PIP_PATH=%VENV_DIR%\Scripts\pip.exe"
set "REQUIREMENTS_FILE=%BASE_DIR%\requirements.txt"
set "PYPROJECT_FILE=%BASE_DIR%\pyproject.toml"
set "UV_ZIP_URL=https://github.com/astral-sh/uv/releases/download/0.10.4/uv-x86_64-pc-windows-msvc.zip"
set "UV_ZIP_PATH=%TEMP%\uv.zip"
set "UV_DIR=%USERPROFILE%\.uv"

:: Detect Python first
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python and add it to PATH.
    pause
    exit /b 1
)

:: Check Google connectivity through proxy
set "USE_PROXY=0"
set "PROXY_URL=http://127.0.0.1:7890"
echo Checking network connectivity...

:: Added -k (insecure) to bypass SSL issues and removed -I for better compatibility with some proxies
curl -s -k -L --connect-timeout 5 --proxy %PROXY_URL% https://www.google.com >nul 2>nul
if !errorlevel! equ 0 (
    echo [INFO] Proxy connection successful
    set "USE_PROXY=1"
    set "HTTP_PROXY=%PROXY_URL%"
    set "HTTPS_PROXY=%PROXY_URL%"
) else (
    echo [WARN] Proxy connection failed
    set "USE_PROXY=0"
    set "HTTP_PROXY="
    set "HTTPS_PROXY="
)

:: Setup curl proxy argument
set "CURL_PROXY="
if "%USE_PROXY%"=="1" (
    set "CURL_PROXY=--proxy %PROXY_URL% -k"
)

:: Detect uv
where uv >nul 2>&1
if !errorlevel! neq 0 (
    echo [INFO] Installing uv...
    curl -L !CURL_PROXY! --connect-timeout 30 --retry 3 -o "%UV_ZIP_PATH%" "%UV_ZIP_URL%"

    if !errorlevel! equ 0 (
        if not exist "%UV_DIR%" mkdir "%UV_DIR%"
        powershell -Command "Expand-Archive -Path '%UV_ZIP_PATH%' -DestinationPath '%UV_DIR%' -Force"
        del "%UV_ZIP_PATH%" 2>nul
        set "PATH=%UV_DIR%;%PATH%"
    ) else (
        echo [ERROR] uv download failed.
        del "%UV_ZIP_PATH%" 2>nul
        pause
        exit /b 1
    )
)

echo [INFO] Creating virtual environment...
where uv >nul 2>&1
if %errorlevel% equ 0 (
    uv venv "%VENV_DIR%" >nul 2>&1
    if !errorlevel! equ 0 (
        echo [INFO] Virtual environment created with uv
        set "USE_UV=1"
        goto :sync_start
    )
)

:use_python_venv
echo [INFO] Creating virtual environment with Python...
python -m venv "%VENV_DIR%"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)
set "USE_UV="

:sync_start
echo [INFO] Syncing dependencies...
cd /d "%BASE_DIR%"

:: Define index URL (Use mirror only if NOT using proxy)
set "PIP_INDEX=-i https://mirrors.aliyun.com/pypi/simple/"
if "%USE_PROXY%"=="1" set "PIP_INDEX="

if exist "requirements.txt" (
    if defined USE_UV (
        uv pip install -r requirements.txt !PIP_INDEX!
    ) else (
        "%VENV_DIR%\Scripts\pip.exe" install -r requirements.txt !PIP_INDEX!
    )
    goto :sync_check
)

if exist "pyproject.toml" (
    if defined USE_UV (
        uv pip install -e . !PIP_INDEX!
    ) else (
        "%VENV_DIR%\Scripts\pip.exe" install . !PIP_INDEX!
    )
    goto :sync_check
)

echo [ERROR] Requirements file not found.
pause
exit /b 1

:sync_check
if %errorlevel% equ 0 (
    echo [SUCCESS] Dependencies synced successfully.
) else (
    echo [ERROR] Dependencies sync failed.
    pause
    exit /b 1
)

exit /b 0