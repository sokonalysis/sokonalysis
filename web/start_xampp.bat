@echo off
echo Starting XAMPP services...

REM Start Apache
net start Apache2.4 2>nul
if %errorlevel% == 0 (
    echo Apache started successfully
) else (
    echo Apache might already be running or failed to start
)

REM Start MySQL
net start MySQL 2>nul
if %errorlevel% == 0 (
    echo MySQL started successfully
) else (
    echo MySQL might already be running or failed to start
)

echo.
echo XAMPP services startup complete.
echo You can now access the application at: http://localhost/sokonalysisWEB/
echo.
pause