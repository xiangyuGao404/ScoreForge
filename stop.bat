@echo off
chcp 65001 >nul 2>&1

:: ScoreForge 停止脚本 (Windows)
:: 用法: 双击 stop.bat

echo 正停止 ScoreForge 服务...

:: 停止后端 (uvicorn)
tasklist /fi "windowtitle eq ScoreForge-Backend" 2>nul | findstr "cmd.exe" >nul 2>&1
if %errorlevel%==0 (
    taskkill /fi "windowtitle eq ScoreForge-Backend" /f >nul 2>&1
    echo   后端已停止 ✓
) else (
    echo   后端未在运行
)

:: 停止前端 (node)
tasklist /fi "windowtitle eq ScoreForge-Frontend" 2>nul | findstr "cmd.exe" >nul 2>&1
if %errorlevel%==0 (
    taskkill /fi "windowtitle eq ScoreForge-Frontend" /f >nul 2>&1
    echo   前端已停止 ✓
) else (
    echo   前端未在运行
)

:: 兜底: 杀掉占用端口的进程
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    taskkill /pid %%a /f >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173 " ^| findstr "LISTENING"') do (
    taskkill /pid %%a /f >nul 2>&1
)

echo.
echo 已停止所有 ScoreForge 服务
pause
