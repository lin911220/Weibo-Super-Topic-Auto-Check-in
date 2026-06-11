@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo   weibo checkin - relogin
echo ============================================
echo.
echo Browser will open. Please scan QR Code with Weibo APP to login
echo.

call myenv\Scripts\activate.bat
python auth.py

echo.
if %errorlevel% equ 0 (
    echo ============================================
    echo   Login success! Cookie updated to GCS
    echo ============================================
) else (
    echo ============================================
    echo   Login failed, please check the error above
    echo ============================================
)
echo.
pause