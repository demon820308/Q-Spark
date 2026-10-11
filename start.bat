@echo off
@chcp 65001 >nul 2>nul
@pushd "%~dp0"

taskkill /F /IM sd-server.exe /T >nul 2>nul
taskkill /F /IM sd-cli.exe /T >nul 2>nul

if exist "%~dp0python_embeded\python.exe" (
    "%~dp0python_embeded\python.exe" -s app.py
) else (
    python app.py
)

if %ERRORLEVEL% neq 0 (
    echo.
    echo If you see this and Q-Spark Studio did not start try updating your Nvidia Drivers to the latest.
    echo If you get a dll error you need to install vc redist that you can find: https://aka.ms/vc14/vc_redist.x64.exe
)
pause
