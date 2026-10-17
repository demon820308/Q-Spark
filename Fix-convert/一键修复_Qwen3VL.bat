@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

set "PY_EXE="
if exist "%~dp0python_embeded\python.exe" set "PY_EXE=%~dp0python_embeded\python.exe"
if not defined PY_EXE if exist "%~dp0..\python_embeded\python.exe" set "PY_EXE=%~dp0..\python_embeded\python.exe"
if not defined PY_EXE if exist "K:\ComfyUi\ComfyUI\python_embeded\python.exe" set "PY_EXE=K:\ComfyUi\ComfyUI\python_embeded\python.exe"
if not defined PY_EXE if exist "K:\ComfyUi\ComfyUI\.venv\Scripts\python.exe" set "PY_EXE=K:\ComfyUi\ComfyUI\.venv\Scripts\python.exe"
if not defined PY_EXE set "PY_EXE=python"

"%PY_EXE%" -u "%~dp0convert_qwen3vl.py" %*

pause
