@echo off
echo Starting Image Privacy Guardian...
echo 正在启动图像隐私守护者...

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    echo Python未安装或不在系统路径中
    pause
    exit /b 1
)

REM 启动应用程序
python main.py

pause