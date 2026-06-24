@echo off
cd /d "%~dp0"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.
echo Bibliotecas instaladas.
echo Agora copie .env.example para .env e adicione sua chave.
pause
