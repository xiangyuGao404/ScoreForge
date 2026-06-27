@echo off
setlocal enabledelayedexpansion

echo.
echo ==========================================
echo   ScoreForge - Stop Services
echo ==========================================
echo.

set FOUND=0

:: Check port 8000
set PORT_PID=
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    set PORT_PID=%%a
)
if defined PORT_PID (
    echo   Stopping port 8000 (PID: !PORT_PID!)...
    taskkill /pid !PORT_PID! /f /t >nul 2>&1
    set FOUND=1
    echo   [OK]
) else (
    echo   Port 8000 is not running
)

:: Check port 5173
set PORT_PID=
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":5173 " ^| findstr "LISTENING"') do (
    set PORT_PID=%%a
)
if defined PORT_PID (
    echo   Stopping port 5173 (PID: !PORT_PID!)...
    taskkill /pid !PORT_PID! /f /t >nul 2>&1
    set FOUND=1
    echo   [OK]
) else (
    echo   Port 5173 is not running
)

echo.
if !FOUND!==1 (
    echo   Services stopped.
) else (
    echo   No services to stop.
)
echo.
pause
