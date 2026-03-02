@echo off
chcp 65001 >nul
echo ========================================
echo   文件夹同步到U盘工具
echo ========================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python，请先安装Python 3.6+
    pause
    exit /b 1
)

if not exist "config.txt" (
    echo [提示] 未找到配置文件 config.txt
    echo [提示] 将使用 config_example.txt 创建示例配置
    copy config_example.txt config.txt >nul
    echo.
    echo [提示] 请编辑 config.txt 文件，设置源文件夹和目标文件夹路径
    echo.
    notepad config.txt
    echo.
    echo [提示] 配置完成后，请重新运行此脚本
    pause
    exit /b 1
)

echo 开始同步...
echo.

python sync_to_upan.py --config config.txt

echo.
echo 按任意键退出...
pause >nul
