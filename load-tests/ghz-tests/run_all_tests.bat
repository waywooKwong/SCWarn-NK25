@echo off
setlocal enabledelayedexpansion

:: Online Boutique gRPC 性能测试主脚本 (Windows版)
:: 此脚本将运行对所有微服务的性能测试，并生成测试报告

:: 设置颜色输出
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "NC=[0m"

:: 基础设置
set "SCRIPT_DIR=%~dp0"
set "PROTO_FILE=%SCRIPT_DIR%..\protos\demo.proto"
set "CONFIG_DIR=%SCRIPT_DIR%configs"
set "SCRIPTS_DIR=%SCRIPT_DIR%scripts"
set "TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "TIMESTAMP=%TIMESTAMP: =0%"
set "RESULTS_DIR=%SCRIPT_DIR%results\%TIMESTAMP%"

:: 创建结果目录
if not exist "%RESULTS_DIR%" mkdir "%RESULTS_DIR%"
echo %GREEN%测试结果将保存在: %RESULTS_DIR%%NC%

:: 日志文件
set "LOG_FILE=%RESULTS_DIR%\test_log.txt"
type nul > "%LOG_FILE%"

:: 记录系统信息
echo ===== 系统信息 ===== >> "%LOG_FILE%"
echo 日期: %date% %time% >> "%LOG_FILE%"
echo 主机名: %COMPUTERNAME% >> "%LOG_FILE%"
echo ================ >> "%LOG_FILE%"

:: 检查ghz是否已安装
where ghz >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo %RED%错误: ghz 未安装. 请先安装ghz工具.%NC%
    echo 可以从 https://github.com/bojand/ghz/releases 下载 >> "%LOG_FILE%"
    exit /b 1
)

:: 检查proto文件是否存在
if not exist "%PROTO_FILE%" (
    echo %RED%错误: proto文件不存在: %PROTO_FILE%%NC%
    exit /b 1
)

:: 检查kubectl是否已安装
where kubectl >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo %RED%错误: kubectl 未安装. 请先安装kubectl工具.%NC%
    exit /b 1
)

:: 检查k8s集群是否可访问
kubectl cluster-info >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo %RED%错误: 无法访问Kubernetes集群. 请确保您已连接到集群.%NC%
    exit /b 1
)

:: 检查online-boutique命名空间是否存在
kubectl get namespace online-boutique >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo %RED%错误: online-boutique 命名空间不存在.%NC%
    exit /b 1
)

:: 主测试流程
echo %GREEN%开始 Online Boutique 微服务 gRPC 性能测试%NC%

:: 检查关键服务的健康状态
echo.
echo %YELLOW%==== 检查服务健康状态 ====%NC%
set "services=productcatalogservice cartservice recommendationservice shippingservice checkoutservice paymentservice"
set "all_healthy=true"

for %%s in (%services%) do (
    echo %YELLOW%检查服务健康状态: %%s%NC%
    kubectl get svc -n online-boutique %%s >nul 2>nul
    if %ERRORLEVEL% neq 0 (
        echo %RED%错误: 服务 %%s 不存在%NC%
        set "all_healthy=false"
    ) else (
        for /f "tokens=*" %%p in ('kubectl get pods -n online-boutique -l app^=%%s -o jsonpath^="{.items[0].status.phase}"') do (
            if not "%%p"=="Running" (
                echo %RED%错误: 服务 %%s 的Pod不在运行状态 (当前状态: %%p)%NC%
                set "all_healthy=false"
            ) else (
                echo %GREEN%服务 %%s 健康状态正常%NC%
            )
        )
    )
)

if "%all_healthy%"=="false" (
    echo.
    echo %YELLOW%警告: 某些服务可能不健康，测试结果可能不准确%NC%
    set /p continue_testing="是否继续测试? (y/n) "
    if /i not "%continue_testing%"=="y" (
        echo %RED%测试已取消%NC%
        exit /b 1
    )
)

:: 运行所有单独测试脚本
echo.
echo %YELLOW%==== 运行所有测试脚本 ====%NC%

:: 由于Windows批处理脚本限制，我们使用Git Bash来运行测试脚本
where bash >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo %RED%错误: 未找到bash. 请安装Git Bash或WSL%NC%
    exit /b 1
)

:: 运行所有测试脚本
for %%f in ("%SCRIPTS_DIR%\*.sh") do (
    echo %GREEN%运行脚本: %%f%NC%
    bash "%%f" "%RESULTS_DIR%"
    
    :: 在测试脚本之间添加一些延迟，让系统恢复
    echo %YELLOW%等待系统恢复 (15秒)...%NC%
    timeout /t 15 /nobreak >nul
)

:: 创建测试结果摘要
echo.
echo %YELLOW%==== 创建测试摘要 ====%NC%
set "summary_file=%RESULTS_DIR%\summary.html"

echo ^<!DOCTYPE html^> > "%summary_file%"
echo ^<html^> >> "%summary_file%"
echo ^<head^> >> "%summary_file%"
echo     ^<title^>Online Boutique gRPC 性能测试结果^</title^> >> "%summary_file%"
echo     ^<style^> >> "%summary_file%"
echo         body { font-family: Arial, sans-serif; margin: 20px; } >> "%summary_file%"
echo         h1, h2 { color: #333; } >> "%summary_file%"
echo         table { border-collapse: collapse; width: 100%%; margin-top: 20px; } >> "%summary_file%"
echo         th, td { border: 1px solid #ddd; padding: 8px; text-align: left; } >> "%summary_file%"
echo         th { background-color: #f2f2f2; } >> "%summary_file%"
echo         tr:hover { background-color: #f5f5f5; } >> "%summary_file%"
echo         .success { color: green; } >> "%summary_file%"
echo         .failure { color: red; } >> "%summary_file%"
echo     ^</style^> >> "%summary_file%"
echo ^</head^> >> "%summary_file%"
echo ^<body^> >> "%summary_file%"
echo     ^<h1^>Online Boutique gRPC 性能测试结果^</h1^> >> "%summary_file%"
echo     ^<p^>测试时间: %date% %time%^</p^> >> "%summary_file%"
echo     >> "%summary_file%"
echo     ^<h2^>测试结果文件^</h2^> >> "%summary_file%"
echo     ^<table^> >> "%summary_file%"
echo         ^<tr^> >> "%summary_file%"
echo             ^<th^>服务^</th^> >> "%summary_file%"
echo             ^<th^>方法^</th^> >> "%summary_file%"
echo             ^<th^>结果文件^</th^> >> "%summary_file%"
echo         ^</tr^> >> "%summary_file%"

:: 添加每个测试结果文件的链接
for %%f in ("%RESULTS_DIR%\*.html") do (
    if not "%%~nxf"=="summary.html" (
        for /f "tokens=1,2 delims=_" %%a in ("%%~nxf") do (
            echo         ^<tr^> >> "%summary_file%"
            echo             ^<td^>%%a^</td^> >> "%summary_file%"
            echo             ^<td^>%%b^</td^> >> "%summary_file%"
            echo             ^<td^>^<a href="%%~nxf"^>%%~nxf^</a^>^</td^> >> "%summary_file%"
            echo         ^</tr^> >> "%summary_file%"
        )
    )
)

echo     ^</table^> >> "%summary_file%"

:: 添加测试日志
echo     ^<h2^>测试日志^</h2^> >> "%summary_file%"
echo     ^<pre^> >> "%summary_file%"
type "%LOG_FILE%" >> "%summary_file%"
echo     ^</pre^> >> "%summary_file%"

echo ^</body^> >> "%summary_file%"
echo ^</html^> >> "%summary_file%"

echo %GREEN%测试摘要已创建: %summary_file%%NC%

echo.
echo %GREEN%所有测试已完成！%NC%
echo %GREEN%测试结果目录: %RESULTS_DIR%%NC%
echo %GREEN%测试摘要: %summary_file%%NC%

endlocal 