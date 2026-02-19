@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

set "VENV_DIR=src\.venv"
set "VENV_ACTIVATE=!VENV_DIR!\Scripts\activate.bat"
set "PIP_PATH=!VENV_DIR!\Scripts\pip.exe"
set "REQUIREMENTS_FILE=src\requirements.txt"
set "PYPROJECT_FILE=src\pyproject.toml"

where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装uv...
    powershell -Command "try { Invoke-WebRequest -Uri https://github.com/astral-sh/uv/releases/latest/download/uv-windows-x86_64.zip -OutFile uv.zip; Expand-Archive uv.zip -DestinationPath %USERPROFILE%\.uv; del uv.zip } catch { echo uv安装失败，将使用pip同步依赖 }"
    set "PATH=%USERPROFILE%\.uv;%PATH%"
    where uv >nul 2>&1
    if %errorlevel% neq 0 (
        echo uv安装失败，将使用pip同步依赖
        set "USE_PIP=1"
    ) else (
        echo uv安装成功
    )
)

echo 正在创建虚拟环境...
uv venv !VENV_DIR! >nul 2>&1
if %errorlevel% equ 0 (
    echo 成功使用uv创建虚拟环境
) else (
    echo uv创建虚拟环境失败
    echo 正在使用Python创建虚拟环境...
    where python >nul 2>&1
    if %errorlevel% neq 0 (
        echo 未检测到Python，请先安装并添加到环境变量
        pause
        exit 1
    )
    python -m venv !VENV_DIR!
    if %errorlevel% neq 0 (
        echo 无法创建虚拟环境
        pause
        exit 1
    )
    echo 成功使用Python创建虚拟环境
    set "USE_PIP=1"
)

echo 正在同步依赖...
if exist !REQUIREMENTS_FILE! (
    if defined USE_PIP (
        %PIP_PATH% install -r !REQUIREMENTS_FILE!
    ) else (
        uv sync --file !REQUIREMENTS_FILE!
    )
    if %errorlevel% equ 0 (
        echo 成功同步依赖
    ) else (
        echo 同步依赖失败
        pause
        exit 1
    )
) else if exist !PYPROJECT_FILE! (
    if defined USE_PIP (
        %PIP_PATH% install ./src
    ) else (
         cd src && uv sync && cd ..
    )
    if %errorlevel% equ 0 (
        echo 成功同步依赖
    ) else (
        echo 同步依赖失败
        pause
        exit 1
    )
) else (
    echo 未找到依赖文件
    pause
    exit 1
)

echo 依赖同步完成
pause
exit 0