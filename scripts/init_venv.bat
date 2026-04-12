@echo off
setlocal

set "BASE_DIR=%~dp0..\"
set "VENV_DIR=%BASE_DIR%\.venv"
set "VENV_ACTIVATE=%VENV_DIR%\Scripts\activate.bat"
set "PIP_PATH=%VENV_DIR%\Scripts\pip.exe"
set "REQUIREMENTS_FILE=%BASE_DIR%\requirements.txt"
set "PYPROJECT_FILE=%BASE_DIR%\pyproject.toml"

:: Detect Python first
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Please install Python and add it to PATH.
    pause
    exit /b 1
)

:: Detect uv
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing uv...
    powershell -Command "try { Invoke-WebRequest -Uri https://github.com/astral-sh/uv/releases/download/0.10.4/uv-x86_64-pc-windows-msvc.zip -OutFile uv.zip; Expand-Archive uv.zip -DestinationPath %USERPROFILE%\.uv -Force; del uv.zip } catch { echo 'uv install failed' }"
    set "PATH=%USERPROFILE%\.uv;%PATH%"
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
if exist "%BASE_DIR%requirements.txt" (
    if defined USE_UV (
        uv pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
    ) else (
        "%VENV_DIR%\Scripts\pip.exe" install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
    )
    goto :sync_check
)

if exist "%BASE_DIR%pyproject.toml" (
    if defined USE_UV (
        uv pip install -e . -i https://mirrors.aliyun.com/pypi/simple/
    ) else (
        "%VENV_DIR%\Scripts\pip.exe" install . -i https://mirrors.aliyun.com/pypi/simple/
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
