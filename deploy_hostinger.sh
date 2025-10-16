#!/bin/bash

# ============================================================================
# AudioMedic - Script de Deploy Automatizado para Hostinger VPS
# ============================================================================

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         🚀 AudioMedic - Deploy Automatizado                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
PROJECT_DIR="/var/www/audiomedic"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
LOG_DIR="/var/log/audiomedic"

# Functions
log_info() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Este script deve ser executado como root (sudo)"
        exit 1
    fi
}

# Step 1: Check if running as root
check_root
log_info "Executando como root"

# Step 2: Update system
echo ""
echo "📦 Atualizando sistema..."
apt update -y
log_info "Sistema atualizado"

# Step 3: Install system dependencies
echo ""
echo "📦 Instalando dependências do sistema..."
apt install -y git curl wget software-properties-common build-essential nginx supervisor

# Install Python 3.11
if ! command -v python3.11 &> /dev/null; then
    add-apt-repository ppa:deadsnakes/ppa -y
    apt update
    apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
    log_info "Python 3.11 instalado"
else
    log_info "Python 3.11 já instalado"
fi

# Install Node.js 18
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt install -y nodejs
    log_info "Node.js instalado"
else
    log_info "Node.js já instalado"
fi

# Install Yarn
if ! command -v yarn &> /dev/null; then
    npm install -g yarn
    log_info "Yarn instalado"
else
    log_info "Yarn já instalado"
fi

# Step 4: Create project directory
echo ""
echo "📁 Configurando diretórios..."
mkdir -p $PROJECT_DIR
mkdir -p $LOG_DIR
log_info "Diretórios criados"

# Step 5: Copy files (assuming current directory has the files)
echo ""
echo "📋 Copiando arquivos do projeto..."
if [ -d "./backend" ] && [ -d "./frontend" ]; then
    cp -r ./backend $PROJECT_DIR/
    cp -r ./frontend $PROJECT_DIR/
    log_info "Arquivos copiados"
else
    log_warn "Diretórios backend/frontend não encontrados no diretório atual"
    log_warn "Por favor, copie manualmente ou clone do repositório"
    exit 1
fi

# Step 6: Configure Backend
echo ""
echo "🐍 Configurando Backend..."
cd $BACKEND_DIR

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
log_info "Dependências Python instaladas"

# Check if .env exists
if [ ! -f ".env" ]; then
    log_warn "Arquivo .env não encontrado no backend"
    log_warn "Criando template .env - CONFIGURE ANTES DE PROSSEGUIR"
    
    cat > .env << 'EOF'
# MongoDB - CONFIGURE AQUI
MONGO_URL=mongodb://localhost:27017
DB_NAME=audiomedic_db

# CORS - Adicione seu domínio
CORS_ORIGINS=https://seudominio.com

# JWT - GERE UMA CHAVE SEGURA
JWT_SECRET=GERAR_STRING_ALEATORIA_64_CHARS
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# OpenAI - Adicione suas chaves
EMERGENT_LLM_KEY=
OPENAI_API_KEY=

# SMTP - Configure para envio de emails
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=noreply@seudominio.com
SMTP_FROM_NAME=AudioMedic
SMTP_USE_TLS=true

# Frontend URL
FRONTEND_URL=https://seudominio.com
EOF
    
    # Generate JWT secret
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
    sed -i "s/JWT_SECRET=.*/JWT_SECRET=$JWT_SECRET/" .env
    
    log_warn "Arquivo .env criado em $BACKEND_DIR/.env"
    log_warn "EDITE O ARQUIVO .env ANTES DE CONTINUAR!"
    echo ""
    read -p "Pressione ENTER após editar o .env para continuar..."
fi

deactivate
log_info "Backend configurado"

# Step 7: Configure Frontend
echo ""
echo "⚛️  Configurando Frontend..."
cd $FRONTEND_DIR

# Install dependencies
yarn install
log_info "Dependências Node instaladas"

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    log_warn "Criando .env.production - CONFIGURE SEU DOMÍNIO"
    
    cat > .env.production << 'EOF'
REACT_APP_BACKEND_URL=https://seudominio.com
REACT_APP_ENABLE_VISUAL_EDITS=false
ENABLE_HEALTH_CHECK=false
EOF
    
    log_warn "Arquivo .env.production criado"
    echo ""
    read -p "Edite $FRONTEND_DIR/.env.production se necessário. Pressione ENTER para continuar..."
fi

# Build production
yarn build
log_info "Frontend build gerado"

# Step 8: Configure Supervisor
echo ""
echo "⚙️  Configurando Supervisor..."

cat > /etc/supervisor/conf.d/audiomedic-backend.conf << EOF
[program:audiomedic-backend]
directory=$BACKEND_DIR
command=$BACKEND_DIR/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=$LOG_DIR/backend.err.log
stdout_logfile=$LOG_DIR/backend.out.log
environment=PATH="$BACKEND_DIR/venv/bin"
EOF

supervisorctl reread
supervisorctl update
log_info "Supervisor configurado"

# Step 9: Configure Nginx
echo ""
echo "🌐 Configurando Nginx..."

# Ask for domain
read -p "Digite seu domínio (ex: audiomedic.com): " DOMAIN

if [ -z "$DOMAIN" ]; then
    DOMAIN="audiomedic.example.com"
    log_warn "Usando domínio padrão: $DOMAIN"
fi

cat > /etc/nginx/sites-available/audiomedic << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    root $FRONTEND_DIR/build;
    index index.html;
    
    # Frontend routes
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    # Backend API proxy
    location /api/ {
        proxy_pass http://localhost:8001/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
    
    # Static files cache
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    access_log /var/log/nginx/audiomedic_access.log;
    error_log /var/log/nginx/audiomedic_error.log;
}
EOF

# Remove default site
rm -f /etc/nginx/sites-enabled/default

# Enable AudioMedic site
ln -sf /etc/nginx/sites-available/audiomedic /etc/nginx/sites-enabled/

# Test Nginx config
nginx -t

# Restart Nginx
systemctl restart nginx
log_info "Nginx configurado"

# Step 10: Configure Firewall
echo ""
echo "🔥 Configurando Firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
log_info "Firewall configurado"

# Step 11: Set permissions
echo ""
echo "🔐 Configurando permissões..."
chown -R www-data:www-data $PROJECT_DIR
chown -R www-data:www-data $LOG_DIR
log_info "Permissões configuradas"

# Step 12: Start services
echo ""
echo "🚀 Iniciando serviços..."
supervisorctl start audiomedic-backend
systemctl restart nginx
log_info "Serviços iniciados"

# Step 13: Setup SSL (optional)
echo ""
read -p "Deseja configurar SSL/HTTPS com Let's Encrypt? (s/n): " SETUP_SSL

if [ "$SETUP_SSL" = "s" ] || [ "$SETUP_SSL" = "S" ]; then
    apt install -y certbot python3-certbot-nginx
    certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --register-unsafely-without-email || {
        log_warn "Certbot falhou. Configure manualmente: certbot --nginx -d $DOMAIN"
    }
    log_info "SSL configurado"
fi

# Final summary
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              ✅ Deploy Concluído com Sucesso!               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
log_info "AudioMedic está rodando!"
echo ""
echo "📝 Próximos passos:"
echo "   1. Acesse: http://$DOMAIN (ou https:// se SSL configurado)"
echo "   2. Crie usuário admin:"
echo "      cd $BACKEND_DIR"
echo "      source venv/bin/activate"
echo "      python3 create_admin.py"
echo ""
echo "📊 Comandos úteis:"
echo "   - Ver logs backend: tail -f $LOG_DIR/backend.err.log"
echo "   - Status backend: supervisorctl status audiomedic-backend"
echo "   - Restart backend: supervisorctl restart audiomedic-backend"
echo "   - Restart nginx: systemctl restart nginx"
echo ""
echo "📖 Documentação completa: DEPLOY_HOSTINGER.md"
echo ""
