#!/bin/bash
set -e

# ==============================================================================
# Script de Deploy do ServConecta no Servidor de Produção
# Caminho: /www/wwwroot/serv-conecta
# ==============================================================================

# Garantir que o binário do uv seja encontrado no PATH da sessão SSH
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/root/.local/bin:/usr/local/bin:$PATH"

APP_DIR="/www/wwwroot/serv-conecta"

echo "=== [1/5] Acessando diretório da aplicação: $APP_DIR ==="
cd "$APP_DIR"

echo "=== [2/5] Baixando atualizações do Git (branch master) ==="
git pull origin master

echo "=== [3/5] Atualizando dependências com uv ==="
if command -v uv &> /dev/null; then
    uv sync
    echo "=== [4/5] Executando migrações do banco e coletando estáticos com uv ==="
    uv run manage.py migrate --noinput
    uv run manage.py collectstatic --noinput
else
    echo "Aviso: 'uv' não encontrado no PATH. Utilizando python da venv local..."
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    elif [ -d "venv" ]; then
        source venv/bin/activate
    fi
    pip install -r requirements.txt
    echo "=== [4/5] Executando migrações do banco e coletando estáticos ==="
    python manage.py migrate --noinput
    python manage.py collectstatic --noinput
fi

echo "=== [5/5] Reiniciando serviço Gunicorn no Supervisor / systemd ==="
if command -v supervisorctl &> /dev/null; then
    echo "Reiniciando aplicação via Supervisor..."
    supervisorctl restart serv-conecta || supervisorctl restart servconecta || supervisorctl restart all
elif systemctl is-active --quiet servconecta; then
    sudo systemctl restart servconecta
    echo "Serviço systemd 'servconecta' reiniciado."
else
    echo "Aviso: Nenhum gerenciador de serviço encontrado. Atualizando tmp/restart.txt."
    mkdir -p tmp && touch tmp/restart.txt
fi

echo "=== Deploy concluído com sucesso! ==="
