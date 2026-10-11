@echo off
@chcp 65001 >nul 2>nul
@pushd "%~dp0"

echo ========================================================
echo   Q-Spark Studio (Port: 40188)
echo ========================================================
echo.
echo Starting Studio Server...
echo Web UI:    http://127.0.0.1:40188
echo Agent API: http://127.0.0.1:40188/v1/images/generations
echo.
echo [提示] 服务启动完成后，将自动在浏览器打开 Web 界面...
echo.
if exist "%~dp0python_embeded\python.exe" (
    set "PYTHON_CMD=%~dp0python_embeded\python.exe"
) else (
    set "PYTHON_CMD=python"
)

"%PYTHON_CMD%" app.py
pause
