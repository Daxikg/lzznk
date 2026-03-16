@echo off
chcp 65001 >nul
echo ========================================
echo    车间设备监控大屏系统 - 一键启动
echo ========================================
echo.

:: 启动Django后端（使用虚拟环境）
echo [1/2] 启动Django后端服务...
start "Django Server" cmd /k "cd /d E:\lzznk && .venv\Scripts\activate && python manage.py runserver 0.0.0.0:10003"

:: 等待2秒
timeout /t 2 /nobreak >nul

:: 启动Vue前端
echo [2/2] 启动Vue前端服务...
start "Vue Dev Server" cmd /k "cd /d E:\大屏展示 && npm run dev -- --host"

echo.
echo ========================================
echo 启动完成！
echo.
echo 后端API: http://localhost:10003
echo 前端页面: http://localhost:20003
echo.
echo 后台管理: http://localhost:10003/admin/
echo ========================================
echo.
pause