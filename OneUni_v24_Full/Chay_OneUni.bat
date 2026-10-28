@echo off
cd /d "%~dp0"
where py >nul 2>nul && (py HUIT_DangKyHocPhan_OneUni_v24.py) || (python HUIT_DangKyHocPhan_OneUni_v24.py)
if errorlevel 1 pause
