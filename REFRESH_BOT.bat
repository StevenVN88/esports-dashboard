@echo off
echo ==========================================
echo   REFRESH SEATALK BOT KNOWLEDGE
echo ==========================================
echo.

cd /d D:\Projects\EsportsAI

echo [1/2] Export summary CSVs tu DuckDB...
python scripts\export_bot_knowledge.py
if %errorlevel% neq 0 (echo LOI: export that bai! & pause & exit /b 1)

echo.
echo [2/2] Upload len Alpha Knowledge Bot...
python scripts\upload_bot_knowledge.py
if %errorlevel% neq 0 (echo LOI: upload that bai! & pause & exit /b 1)

echo.
echo ==========================================
echo   BOT DA DUOC CAP NHAT!
echo ==========================================
pause
