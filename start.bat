@echo off
chcp 65001 >nul
cd /d %~dp0
title 食堂匿名打分系统
if not exist ".venv\Scripts\python.exe" (
    echo [初始化] 首次运行，正在创建虚拟环境并安装依赖...
    python -m venv .venv
    ".venv\Scripts\python.exe" -m pip install flask --quiet --disable-pip-version-check
)
echo.
echo ============================================================
echo   食堂匿名打分系统启动中...
echo   本机访问:  http://127.0.0.1:5001
echo   局域网部署: 修改 app.py 底部 HOST=0.0.0.0 后重新运行
echo ============================================================
echo.
start "" http://127.0.0.1:5001
".venv\Scripts\python.exe" app.py
pause
