@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

:: 1. 路径初始化（确保不含多余反斜杠）
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
set "ROOT_DIR=%~dp0..\"
:: 标准化路径，防止出现 \\ 情况
for %%i in ("%ROOT_DIR%") do set "ROOT_DIR=%%~fi"

set "PACKAGE_LIST=%ROOT_DIR%latex_packages.txt"
set "ZIP_URL=https://github.com/rstudio/tinytex-releases/releases/download/v2026.03.02/TinyTeX-v2026.03.02.zip"
set "ZIP_PATH=%ROOT_DIR%TinyTeX.zip"
set "INSTALL_DIR=%ROOT_DIR%TinyTeX"
set "ARIA2_EXE=%ROOT_DIR%aria2c.exe"

echo 正在配置 LaTeX 环境...

:: 2. 检查并下载 aria2c
if not exist "%ARIA2_EXE%" (
    echo 正在获取下载加速工具 aria2c...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-64bit-build1.zip' -OutFile '%ROOT_DIR%aria2.zip'"

    if not exist "%ROOT_DIR%aria2_temp" mkdir "%ROOT_DIR%aria2_temp"

    :: 使用 tar 直接解压（不使用 strip-components 以免报错）
    tar -xf "%ROOT_DIR%aria2.zip" -C "%ROOT_DIR%aria2_temp"

    :: 精确移动文件：aria2 的 zip 包内部通常有一层同名目录
    for /f "delims=" %%f in ('dir /s /b "%ROOT_DIR%aria2_temp\aria2c.exe"') do (
        move /y "%%f" "%ARIA2_EXE%" >nul
    )

    rd /s /q "%ROOT_DIR%aria2_temp" >nul 2>&1
    del "%ROOT_DIR%aria2.zip" >nul 2>&1
)

:: 3. 下载 TinyTeX
if not exist "%INSTALL_DIR%" (
    echo 正在使用 aria2c 高速下载 TinyTeX...
    "%ARIA2_EXE%" -x 16 -s 16 --check-certificate=false -d "%ROOT_DIR%." -o "TinyTeX.zip" "%ZIP_URL%"

    if !errorlevel! neq 0 (
        echo [警告] aria2c 下载失败，尝试备用方案...
        powershell -Command "Invoke-WebRequest -Uri '%ZIP_URL%' -OutFile '%ZIP_PATH%'"
    )

    echo 正在使用 tar 高速解压...
    if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
    :: 关键：Windows tar 在解压 zip 时，-C 参数后的路径必须存在
    tar -xf "%ZIP_PATH%" -C "%ROOT_DIR%."

    if !errorlevel! equ 0 (
        del "%ZIP_PATH%"
    ) else (
        echo [错误] 解压失败。
        pause
        exit /b 1
    )
)

:: 4. 环境变量与宏包管理
set "PATH=%INSTALL_DIR%\bin\windows;%PATH%"

:: 切换到官方 2026 镜像源（或阿里云）
call tlmgr option repository https://mirrors.aliyun.com/CTAN/systems/texlive/tlnet/

if exist "%PACKAGE_LIST%" (
    echo 正在从列表安装宏包...
    for /f "usebackq tokens=*" %%i in ("%PACKAGE_LIST%") do (
        set "line=%%i"
        :: 检查是否为注释或空行
        set "firstchar=!line:~0,1!"
        if not "!firstchar!"=="#" if not "!line!"=="" (
            echo 正在安装: !line!
            call tlmgr install !line!
        )
    )
)

echo LaTeX 引擎配置完成
exit /b 0