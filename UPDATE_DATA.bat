@echo off
echo ==========================================
echo   ESPORTS ANALYTICS - UPDATE DATA
echo ==========================================
echo.
echo Chon che do:
echo   1 = Thay CSV moi (CSV moi chua TOAN BO data)
echo   2 = Merge CSV moi (CSV moi chi chua DATA MOI, can gop voi data cu)
echo.
set /p mode="Nhap 1 hoac 2: "

cd /d D:\Projects\EsportsAI

if "%mode%"=="2" (
    echo.
    echo [0/6] Merge CSV moi vao data cu...
    echo      Copy CSV moi vao: D:\EsportsAI\data\new\
    echo.
    pause
    python scripts\merge_csv.py
    if %errorlevel% neq 0 (echo LOI: merge_csv.py that bai! & pause & exit /b 1)
)

echo.
echo [1/6] Rebuild Database tu CSV...
python scripts\build_db.py
if %errorlevel% neq 0 (echo LOI: build_db.py that bai! & pause & exit /b 1)

echo.
echo [2/6] Tao base views...
python scripts\build_views.py
if %errorlevel% neq 0 (echo LOI: build_views.py that bai! & pause & exit /b 1)

echo.
echo [3/6] Tao core views...
python scripts\01_core_views.py
if %errorlevel% neq 0 (echo LOI: 01_core_views.py that bai! & pause & exit /b 1)

echo.
echo [4/6] Tao reporting views...
python scripts\02_reporting_views.py
if %errorlevel% neq 0 (echo LOI: 02_reporting_views.py that bai! & pause & exit /b 1)

echo.
echo [5/6] Export + Upload Bot Knowledge (SeaTalk)...
python scripts\export_bot_knowledge.py
if %errorlevel% neq 0 (echo CANH BAO: export that bai, bo qua upload.)
python scripts\upload_bot_knowledge.py
if %errorlevel% neq 0 (echo CANH BAO: upload that bai, check log tren.)

echo.
echo [6/6] Push len GitHub (Streamlit Cloud tu rebuild)...
git add db\esports.duckdb
git commit -m "Data update %date% %time%"
git push

echo.
echo ==========================================
echo   HOAN TAT!
echo   Dashboard : https://aovesports.streamlit.app
echo   Bot CSVs  : D:\EsportsAI\reports\bot_knowledge\
echo ==========================================
pause
