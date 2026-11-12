@echo off
title Setup Windows Task Scheduler for vAPI Network
echo ==============================================================
echo Menambahkan vAPI Network ke Task Scheduler Windows
echo Tugas akan berjalan otomatis setiap hari jam 08:00 Pagi
echo ==============================================================

set SCRIPT_PATH=%~dp0main.py
schtasks /create /tn "vAPINetworkDailyBot" /tr "python \"%SCRIPT_PATH%\"" /sc daily /st 08:00 /f

if %ERRORLEVEL% equ 0 (
    echo.
    echo [SUKSES] Task berhasil didaftarkan ke Windows Task Scheduler!
    echo Bot akan otomatis berjalan setiap jam 08:00 Pagi.
) else (
    echo.
    echo [GAGAL] Pastikan Anda klik kanan dan pilih 'Run as Administrator'.
)
echo.
pause
