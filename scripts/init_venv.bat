@echo off
chcp 65001 >nul 2>&1
setlocal

set "BASE_DIR=%~dp0..\"
set "VENV_DIR=%BASE_DIR%\.venv"
set "VENV_ACTIVATE=%VENV_DIR%\Scripts\activate.bat"
set "PIP_PATH=%VENV_DIR%\Scripts\pip.exe"
set "REQUIREMENTS_FILE=%BASE_DIR%\requirements.txt"
set "PYPROJECT_FILE=%BASE_DIR%\pyproject.toml"

:: 优先检测 Python，确保基础环境可用
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo 未检测到 Python，请先安装并添加到环境变量。
    pause
    exit /b 1
)

:: 检测 uv
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在尝试安装 uv...
    powershell -Command "try { Invoke-WebRequest -Uri https://github.com/astral-sh/uv/releases/download/0.10.4/uv-x86_64-pc-windows-msvc.zip -OutFile uv.zip; Expand-Archive uv.zip -DestinationPath %USERPROFILE%\.uv; del uv.zip } catch { echo uv安装失败 }"
    set "PATH=%USERPROFILE%\.uv;%PATH%"
)

echo 正在创建虚拟环境...
:: 尝试使用 uv 创建
where uv >nul 2>&1
if %errorlevel% equ 0 (
    uv venv "%VENV_DIR%" >nul 2>&1
    if %errorlevel% equ 0 (
        echo 成功使用 uv 创建虚拟环境
        set "USE_UV=1"
        goto :sync_start
    )
)

:use_python_venv
echo 正在使用 Python 创建虚拟环境...
python -m venv %VENV_DIR%
if %errorlevel% neq 0 (
    echo 无法创建虚拟环境。
    pause
    exit /b 1
)
echo 成功使用 Python 创建虚拟环境
set "USE_UV="

:sync_start
echo 正在同步依赖...
if exist "%REQUIREMENTS_FILE%" (
    if defined USE_UV (
        uv sync --file "%REQUIREMENTS_FILE%"
    ) else (
        "%PIP_PATH%" install -r "%REQUIREMENTS_FILE%"
    )
    goto :sync_check
)

if exist "%PYPROJECT_FILE%" (
    if defined USE_UV (
        uv sync --project "%BASE_DIR%src"
    ) else (
        "%PIP_PATH%" install ./src
    )
    goto :sync_check
)

echo 未找到依赖文件
pause
exit /b 1

:sync_check
if %errorlevel% equ 0 (
    echo 成功同步依赖
) else (
    echo 同步依赖失败
    pause
    exit /b 1
)

echo 依赖同步完成
exit /b 0