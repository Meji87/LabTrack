@echo off
title LabTrack Desktop
cd /d "%~dp0"
python main.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] La aplicacion termino con un error.
    echo Ejecuta instalar.bat si es la primera vez.
    pause
)
