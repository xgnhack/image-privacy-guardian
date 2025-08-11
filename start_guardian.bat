@echo off
echo Starting Image Privacy Guardian...
echo Please make sure Python 3.7+ is installed
echo.
python --version
echo.
echo Installing/checking dependencies...
pip install -r requirements.txt
echo.
echo Starting application...
python main.py
pause