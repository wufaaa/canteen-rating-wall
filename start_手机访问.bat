@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Canteen Rating Wall (LAN / phone access)

rem ---- 手机/平板访问版：监听 0.0.0.0，同一 Wi-Fi 下的设备都能打开 ----
rem ---- 用法：双击本文件，然后把下面显示的地址发到手机上 ----

set "HOST=0.0.0.0"
if not defined PORT set "PORT=5001"

rem ---- 显示本机局域网 IP，方便手机输入 ----
echo.
echo  本机局域网地址（手机浏览器输入其中一个是）：
for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr /c:"IPv4"') do (
  for /f "tokens=1" %%a in ("%%i") do echo      http://%%a:%PORT%
)
echo.

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" run.py
) else (
  python run.py
)

echo.
echo Service stopped.
pause
