@echo off
@chcp 65001 >nul 2>nul
@pushd "%~dp0"

echo ========================================================
echo   Stopping Q-Spark Studio and Releasing VRAM...
echo ========================================================
echo.

taskkill /F /IM sd-server.exe /T >nul 2>nul
taskkill /F /IM sd-cli.exe /T >nul 2>nul

for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":40188" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>nul
)

for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":40189" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>nul
)

echo [OK] All Q-Spark processes stopped. VRAM released!
echo.
ping 127.0.0.1 -n 2 >nul
