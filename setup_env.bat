@echo off
echo Setting up Python virtual environment...

REM Check if venv directory exists
if not exist venv (
    echo Creating new virtual environment...
    python -m venv venv
) else (
    echo Virtual environment already exists.
)

REM Activate the virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Environment setup complete!
echo.
echo To test your API key, run:
echo   python test_api_key.py
echo.
echo To deactivate the virtual environment when done, run:
echo   deactivate
echo.

REM Keep the command prompt open
cmd /k
