@echo off
title Instalador LabTrack Desktop
echo.
echo  ============================================
echo   LabTrack Desktop — Instalacion de paquetes
echo  ============================================
echo.

REM Verificar que Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no encontrado.
    echo Descarga Python desde https://www.python.org/downloads/
    echo Asegurate de marcar "Add Python to PATH" durante la instalacion.
    pause
    exit /b 1
)

echo Python encontrado. Instalando dependencias...
echo.

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Hubo un problema durante la instalacion.
    echo Revisa los mensajes de error arriba.
    pause
    exit /b 1
)

echo.
echo  ============================================
echo   Instalacion completada correctamente.
echo   Ahora puedes ejecutar iniciar.bat
echo  ============================================
echo.
pause
