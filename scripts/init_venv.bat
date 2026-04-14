@echo off
setlocal

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
    echo Python not found. Please install Python and add it to PATH.
    pause
    exit /b 1
)

:: Check Google connectivity and set proxy
set "USE_PROXY=0"
set "PROXY_URL=http://127.0.0.1:7890"
echo Checking network connectivity...

curl -s --connect-timeout 3 --max-time 5 -o nul -w "%%{http_code}" https://www.google.com > "%TEMP%\google_test.txt" 2>nul
set /p HTTP_CODE=<"%TEMP%\google_test.txt"
del "%TEMP%\google_test.txt" 2>nul

if "%HTTP_CODE%"=="200" (
    echo Google is accessible, will use proxy: %PROXY_URL%
    set "USE_PROXY=1"
) else (
    echo Google is not accessible, will download directly.
)

:: Setup curl with proxy if needed
set "CURL_PROXY="
if "%USE_PROXY%"=="1" (
    set "CURL_PROXY=--proxy %PROXY_URL%"
)

:: Detect uv
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing uv...
    if "%USE_PROXY%"=="1" (
        curl -L %CURL_PROXY% --connect-timeout 30 --retry 3 -o "%UV_ZIP_PATH%" "%UV_ZIP_URL%"
    ) else (
        curl -L --connect-timeout 30 --retry 3 -o "%UV_ZIP_PATH%" "%UV_ZIP_URL%"
    )

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

echo Creating virtual environment...
:: Try using uv first
where uv >nul 2>&1
if %errorlevel% equ 0 (
    uv venv "%VENV_DIR%" >nul 2>&1
    if %errorlevel% equ 0 (
        echo Virtual environment created with uv
        set "USE_UV=1"
        goto :sync_start
    )
)

:use_python_venv
echo Creating virtual environment with Python...
python -m venv %VENV_DIR%
if %errorlevel% neq 0 (
    echo Failed to create virtual environment.
    pause
    exit /b 1
)
echo Virtual environment created with Python
set "USE_UV="

:sync_start
echo Syncing dependencies...
cd /d "%BASE_DIR%"

:: Setup pip proxy if needed
if "%USE_PROXY%"=="1" (
    set "PIP_PROXY=--proxy %PROXY_URL%"
) else (
    set "PIP_PROXY="
)

if exist "%BASE_DIR%requirements.txt" (
    if defined USE_UV (
        uv pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ %PIP_PROXY%
    ) else (
        "%VENV_DIR%\Scripts\pip.exe" install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ %PIP_PROXY%
    )
    goto :sync_check
)

if exist "%BASE_DIR%pyproject.toml" (
    if defined USE_UV (
        uv pip install -e . -i https://mirrors.aliyun.com/pypi/simple/ %PIP_PROXY%
    ) else (
        "%VENV_DIR%\Scripts\pip.exe" install . -i https://mirrors.aliyun.com/pypi/simple/ %PIP_PROXY%
    )
    goto :sync_check
)

echo Requirements file not found
pause
exit /b 1

:sync_check
if %errorlevel% equ 0 (
    echo Dependencies synced successfully
) else (
    echo Dependencies sync failed
    pause
    exit /b 1
)

echo Dependency sync completed
exit /b 0
