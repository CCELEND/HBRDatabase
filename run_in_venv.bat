@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

:: ===== Configurable parameters =====
set VENV_DIR=venv
set INSTALL_SCRIPT=install_deps.py
set TARGET_SCRIPT=HBRDatabaseGUI_QT.py
:: ===================================

echo [*] Current directory: %cd%

:: 1. Check and create virtual environment if missing
if not exist "%VENV_DIR%\Scripts\activate" (
    echo [*] Virtual environment not found, creating...
    python -m venv %VENV_DIR%
    if errorlevel 1 (
        echo [ERROR] Failed to create venv. Please make sure Python is installed.
        pause
        exit /b 1
    )
    echo [+] Virtual environment created.
)

:: 2. Activate virtual environment
echo [*] Activating virtual environment...
call "%VENV_DIR%\Scripts\activate"
if errorlevel 1 (
    echo [ERROR] Failed to activate venv.
    pause
    exit /b 1
)

:: 3. Install/check dependencies
if exist "%INSTALL_SCRIPT%" (
    echo [*] Installing/checking dependencies via %INSTALL_SCRIPT%...
    python "%INSTALL_SCRIPT%"
    if errorlevel 1 (
        echo [WARN] Dependency installation had issues, continuing...
    )
) else (
    if exist "requirements.txt" (
        echo [*] Found requirements.txt, installing dependencies...
        pip install --upgrade pip
        pip install -r requirements.txt
        if errorlevel 1 (
            echo [WARN] Dependency installation failed, continuing...
        )
    ) else (
        echo [*] No dependency script or requirements.txt found, skipping.
    )
)

:: ========== Fix Qt platform plugin path (using direct path check, no Python call) ==========
echo [*] Setting Qt plugin path...
set "QT_PLUGIN_PATH="

:: Try common locations
if exist "%VENV_DIR%\Lib\site-packages\PyQt5\Qt5\plugins" (
    set "QT_PLUGIN_PATH=%VENV_DIR%\Lib\site-packages\PyQt5\Qt5\plugins"
    goto :set_qt_path
)
if exist "%VENV_DIR%\Lib\site-packages\PyQt5\plugins" (
    set "QT_PLUGIN_PATH=%VENV_DIR%\Lib\site-packages\PyQt5\plugins"
    goto :set_qt_path
)
if exist "%VENV_DIR%\Lib\site-packages\PyQt5\Qt\plugins" (
    set "QT_PLUGIN_PATH=%VENV_DIR%\Lib\site-packages\PyQt5\Qt\plugins"
    goto :set_qt_path
)

echo [*] Could not find Qt plugins in standard locations. Please check PyQt5 installation.
goto :skip_qt_set

:set_qt_path
set "QT_QPA_PLATFORM_PLUGIN_PATH=!QT_PLUGIN_PATH!"
echo [*] Qt plugin path set to: !QT_QPA_PLATFORM_PLUGIN_PATH!

:skip_qt_set
:: ===================================================================================

:: 4. Run target Python script
echo [*] Running %TARGET_SCRIPT% in virtual environment...
python "%TARGET_SCRIPT%"
set EXIT_CODE=%errorlevel%

if %EXIT_CODE% neq 0 (
    echo [ERROR] Script failed with exit code: %EXIT_CODE%
) else (
    echo [+] Script finished successfully.
)

pause
exit /b %EXIT_CODE%