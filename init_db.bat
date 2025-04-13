@echo off
echo Initializing A Fugue In Flask Database
echo =====================================

python -m scripts.init_db

echo.
echo Database initialization completed.
echo You can now run the application with: flask run