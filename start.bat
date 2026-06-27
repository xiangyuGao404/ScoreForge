@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

:: ScoreForge 一键启动脚本 (Windows)
:: 用法: 双击 start.bat 或在 CMD 中执行

set PROJECT_DIR=%~dp0
set BACKEND_DIR=%PROJECT_DIR%backend
set FRONTEND_DIR=%PROJECT_DIR%frontend
set BACKEND_PORT=8000
set FRONTEND_PORT=5173

echo ==========================================
echo   ScoreForge 服务启动
echo ==========================================
echo.

:: 检查端口占用
netstat -ano | findstr ":%BACKEND_PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo [错误] 端口 %BACKEND_PORT% 已被占用
    echo 请先关闭占用该端口的程序
    pause
    exit /b 1
)

netstat -ano | findstr ":%FRONTEND_PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo [错误] 端口 %FRONTEND_PORT% 已被占用
    echo 请先关闭占用该端口的程序
    pause
    exit /b 1
)

:: 启动后端
echo [1/2] 启动后端...
cd /d "%BACKEND_DIR%"
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)
start "ScoreForge-Backend" cmd /c "uvicorn app.main:app --reload --host 0.0.0.0 --port %BACKEND_PORT%"
echo   后端窗口已打开

:: 等待后端就绪
echo   等待后端就绪...
set BACKEND_READY=0
for /l %%i in (1,1,30) do (
    if !BACKEND_READY!==0 (
        curl -s http://localhost:%BACKEND_PORT%/health >nul 2>&1
        if !errorlevel!==0 (
            set BACKEND_READY=1
            echo   后端就绪 ✓
        ) else (
            timeout /t 1 /nobreak >nul
        )
    )
)

if !BACKEND_READY!==0 (
    echo   [警告] 后端启动超时，请检查后端窗口
)

:: 启动前端
echo [2/2] 启动前端...
cd /d "%FRONTEND_DIR%"
start "ScoreForge-Frontend" cmd /c "npm run dev:h5"
echo   前端窗口已打开

:: 等待前端就绪
echo   等待前端就绪...
set FRONTEND_READY=0
for /l %%i in (1,1,30) do (
    if !FRONTEND_READY!==0 (
        curl -s http://localhost:%FRONTEND_PORT% >nul 2>&1
        if !errorlevel!==0 (
            set FRONTEND_READY=1
            echo   前端就绪 ✓
        ) else (
            timeout /t 1 /nobreak >nul
        )
    )
)

if !FRONTEND_READY!==0 (
    echo   [警告] 前端启动超时，请检查前端窗口
)

echo.
echo ==========================================
echo   所有服务已启动
echo.
echo   后端 API:   http://localhost:%BACKEND_PORT%
echo   API 文档:   http://localhost:%BACKEND_PORT%/docs
echo   前端页面:   http://localhost:%FRONTEND_PORT%
echo.
echo   关闭 "ScoreForge-Backend" 和 "ScoreForge-Frontend"
echo   窗口即可停止对应服务
echo ==========================================
echo.

:: 自动打开浏览器
start http://localhost:%FRONTEND_PORT%

pause
