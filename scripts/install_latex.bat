@echo off
chcp 65001 >nul 2>&1
setlocal

set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%..\"
set "PACKAGE_LIST=%ROOT_DIR%latex_packages.txt"
set "ZIP_URL=https://github.com/rstudio/tinytex-releases/releases/download/v2026.02/TinyTeX-1-v2026.02.zip"
set "ZIP_PATH=%ROOT_DIR%TinyTeX.zip"
set "INSTALL_DIR=%ROOT_DIR%TinyTeX"

echo 正在安装 LaTeX 环境...

if not exist "%INSTALL_DIR%" (
    echo 正在下载 TinyTeX 离线包...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%ZIP_URL%' -OutFile '%ZIP_PATH%'"
    if %errorlevel% neq 0 (echo 下载失败 && pause && exit /b 1)

    echo 正在解压...
    powershell -Command "Expand-Archive -Path '%ZIP_PATH%' -DestinationPath '%ROOT_DIR%' -Force"
    del "%ZIP_PATH%"
)

set "PATH=%INSTALL_DIR%\bin\windows;%PATH%"

call tlmgr option repository https://mirrors.aliyun.com/CTAN/systems/texlive/tlnet/

if exist "%PACKAGE_LIST%" (
    echo 正在从列表安装宏包...
    for /f "usebackq tokens=*" %%i in ("%PACKAGE_LIST%") do (
        set "pkg=%%i"
        echo %pkg% | findstr /b "#" >nul
        if errorlevel 1 (
            echo 正在安装: %%i
            call tlmgr install %%i
        )
    )
) else (
    echo 未发现宏包列表文件 %PACKAGE_LIST%。
)

echo LaTeX 引擎配置完成
exit /b 0