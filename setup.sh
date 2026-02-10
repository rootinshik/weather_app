#!/usr/bin/env bash
# Bootstrap development environments for all services
# Usage: bash setup.sh
# Requirements: uv, node, npm

set -e

setup_python() {
    echo ""
    echo "==> $1"
    cd "$1"
    uv venv
    uv pip install -e .
    cd ..
}

setup_python backend
setup_python bot
setup_python ml

echo ""
echo "==> frontend"
cd frontend && npm install && cd ..

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo ".env создан из .env.example — заполни API-ключи."
else
    echo ""
    echo ".env уже существует, пропускаем."
fi

echo ""
echo "Готово! Выбери интерпретатор в VS Code:"
echo "  Ctrl+Shift+P -> Python: Select Interpreter -> backend/.venv/bin/python"
