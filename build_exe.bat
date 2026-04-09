@echo off
setlocal

cd /d "%~dp0"
set TEMP=%~dp0temp
set TMP=%~dp0temp

if not exist "%TEMP%" mkdir "%TEMP%"

echo [1/3] Installing build dependencies...
python -m pip install --no-cache-dir -r requirements.txt
if errorlevel 1 goto :error

echo [2/3] Building executable...
python -m PyInstaller --noconfirm customportrait.spec
if errorlevel 1 goto :error

echo [3/3] Done.
echo Executable: dist\CustomPortraitTool.exe
exit /b 0

:error
echo Build failed.
exit /b 1
