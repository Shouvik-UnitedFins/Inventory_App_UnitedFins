@echo off
echo Uploading updated settings.py to CloudPanel server...
echo.

REM Upload the settings file
scp "python_server\settings.py" iniserve-dev-inventory@91.108.110.230:/home/iniserve-dev-inventory/htdocs/dev.inventory.iniserve.com/python_server/settings.py

echo.
echo Upload completed!
echo.
echo Now run these commands in PuTTY to restart Django:
echo 1. pkill -f "manage.py runserver"
echo 2. nohup python3 manage.py runserver 0.0.0.0:8090 > django.log 2>&1 &
echo.
pause