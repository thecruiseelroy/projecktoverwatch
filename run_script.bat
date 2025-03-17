@echo off
:start
echo Running Middle-Out processor...
python url_middle_out.py
if errorlevel 1 (
    echo Script failed
    pause
    exit /b
)
echo Launching final analysis...
python report_generator.py

:ask_again
echo 1. New search
echo 2. Exit
set /p new_query="Choose an option (1/2): "
if /i "%new_query%"=="1" (
    goto start
) else if /i "%new_query%"=="2" (
    echo Exiting...
    pause
    exit /b
) else (
    echo Please enter 1 or 2
    goto ask_again
) 