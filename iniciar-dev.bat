@echo off
setlocal

rem Garante que os comandos sejam executados na pasta do projeto.
cd /d "%~dp0"

rem Verifica se o Python 3 esta instalado e pode ser executado.
python -c "import sys; raise SystemExit(0 if sys.version_info.major >= 3 else 1)" >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao foi encontrado.
    echo Instale o Python 3 e marque a opcao "Add Python to PATH".
    pause
    exit /b 1
)

rem Evita uma mensagem confusa caso o gerenciador do projeto nao esteja instalado.
where pnpm >nul 2>&1
if errorlevel 1 (
    echo [ERRO] pnpm nao foi encontrado.
    echo Instale-o e tente novamente.
    pause
    exit /b 1
)

echo [OK] Python encontrado. Iniciando o projeto...
pnpm run dev

set "DEV_EXIT_CODE=%ERRORLEVEL%"
if not "%DEV_EXIT_CODE%"=="0" (
    echo.
    echo [ERRO] O servidor foi encerrado com o codigo %DEV_EXIT_CODE%.
    pause
)

exit /b %DEV_EXIT_CODE%
