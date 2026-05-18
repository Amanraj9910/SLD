@echo off 
title SLD Backend Server 
echo ======================================== 
echo   SLD Backend Server 
echo ======================================== 
echo Backend: http://localhost:8000 
echo API Docs: http://localhost:8000/docs 
echo Health: http://localhost:8000/health 
echo. 
set "PYTHONPATH=D:\SLD\SLD\" 
"python" main.py 
