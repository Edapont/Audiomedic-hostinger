#!/bin/bash

# ============================================================================
# AudioMedic - Script de Preparação para Hospedagem Compartilhada
# ============================================================================

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   📦 AudioMedic - Preparar para Hospedagem Compartilhada    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

FRONTEND_DIR="frontend"
BUILD_DIR="frontend/build"
DEPLOY_DIR="deploy_package"

# Função para log
log_info() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# ============================================================================
# 1. Verificar se estamos no diretório correto
# ============================================================================
if [ ! -d "$FRONTEND_DIR" ]; then
    log_error "Diretório frontend não encontrado!"
    log_error "Execute este script da raiz do projeto"
    exit 1
fi

log_info "Diretório correto verificado"

# ============================================================================
# 2. Solicitar URL do Backend
# ============================================================================
echo ""
echo "📝 Configuração do Backend"
echo ""

read -p "URL do backend no Render (ex: https://audiomedic-backend.onrender.com): " BACKEND_URL

if [ -z "$BACKEND_URL" ]; then
    log_error "URL do backend é obrigatória!"
    exit 1
fi

# Remover barra final se existir
BACKEND_URL=${BACKEND_URL%/}

log_info "Backend URL: $BACKEND_URL"

# ============================================================================
# 3. Configurar .env.production
# ============================================================================
echo ""
echo "⚙️  Configurando variáveis de ambiente..."

cat > "$FRONTEND_DIR/.env.production" << EOF
REACT_APP_BACKEND_URL=$BACKEND_URL
REACT_APP_ENABLE_VISUAL_EDITS=false
ENABLE_HEALTH_CHECK=false
EOF

log_info "Arquivo .env.production criado"

# ============================================================================
# 4. Instalar dependências
# ============================================================================
echo ""
echo "📦 Instalando dependências..."

cd "$FRONTEND_DIR"

if ! command -v yarn &> /dev/null; then
    log_warn "Yarn não encontrado. Instalando..."
    npm install -g yarn
fi

yarn install
log_info "Dependências instaladas"

# ============================================================================
# 5. Gerar build de produção
# ============================================================================
echo ""
echo "🏗️  Gerando build de produção..."

yarn build

if [ ! -d "build" ]; then
    log_error "Build falhou! Diretório build/ não foi criado"
    exit 1
fi

log_info "Build gerado com sucesso"

# ============================================================================
# 6. Copiar .htaccess para build
# ============================================================================
echo ""
echo "📋 Copiando .htaccess..."

if [ -f ".htaccess" ]; then
    cp .htaccess build/
    log_info ".htaccess copiado para build/"
else
    log_warn ".htaccess não encontrado. Será necessário criar manualmente."
fi

cd ..

# ============================================================================
# 7. Criar pacote de deploy
# ============================================================================
echo ""
echo "📦 Criando pacote de deploy..."

# Remover pacote anterior se existir
rm -rf "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"

# Copiar build
cp -r "$BUILD_DIR"/* "$DEPLOY_DIR"/

log_info "Pacote criado em: $DEPLOY_DIR/"

# ============================================================================
# 8. Gerar instruções
# ============================================================================
cat > "$DEPLOY_DIR/INSTRUCOES_UPLOAD.txt" << 'EOF'
═══════════════════════════════════════════════════════════
  📤 INSTRUÇÕES DE UPLOAD PARA HOSTINGER
═══════════════════════════════════════════════════════════

1. ACESSE O PAINEL HOSTINGER
   - https://hpanel.hostinger.com/
   - Login com suas credenciais

2. FILE MANAGER
   - Clique em "File Manager"
   - Navegue até "public_html"

3. LIMPAR ARQUIVOS ANTIGOS
   - Selecione TODOS os arquivos em public_html
   - Delete (exceto .htaccess se já existir)

4. UPLOAD DOS ARQUIVOS
   - Clique em "Upload"
   - Selecione TODOS os arquivos desta pasta (deploy_package)
   - Aguarde upload completar (pode demorar alguns minutos)

5. VERIFICAR ESTRUTURA
   Após upload, public_html deve conter:
   ├── index.html
   ├── .htaccess
   ├── static/
   │   ├── css/
   │   ├── js/
   │   └── media/
   ├── manifest.json
   ├── favicon.ico
   └── robots.txt

6. CONFIGURAR SSL (se não fez)
   - No painel Hostinger
   - SSL → Instalar SSL gratuito
   - Aguardar ativação (até 15min)

7. TESTAR
   - Acesse: https://seudominio.com
   - Deve carregar a landing page
   - Testar login e funcionalidades

8. TROUBLESHOOTING
   - Se der erro 404 em rotas: verificar .htaccess
   - Se não carregar: limpar cache do navegador (Ctrl+Shift+R)
   - Se CORS error: verificar CORS_ORIGINS no backend (Render)

═══════════════════════════════════════════════════════════
  ℹ️  SUPORTE
═══════════════════════════════════════════════════════════

Documentação completa: DEPLOY_HOSTINGER_SHARED.md

═══════════════════════════════════════════════════════════
EOF

log_info "Instruções criadas: $DEPLOY_DIR/INSTRUCOES_UPLOAD.txt"

# ============================================================================
# 9. Criar arquivo ZIP (opcional)
# ============================================================================
echo ""
read -p "Deseja criar um arquivo ZIP do pacote? (s/n): " CREATE_ZIP

if [ "$CREATE_ZIP" = "s" ] || [ "$CREATE_ZIP" = "S" ]; then
    ZIP_NAME="audiomedic-frontend-$(date +%Y%m%d-%H%M%S).zip"
    
    if command -v zip &> /dev/null; then
        cd "$DEPLOY_DIR"
        zip -r "../$ZIP_NAME" . > /dev/null
        cd ..
        log_info "ZIP criado: $ZIP_NAME"
        log_info "Você pode fazer upload deste ZIP diretamente no File Manager"
    else
        log_warn "Comando 'zip' não encontrado. Pulando criação do ZIP."
    fi
fi

# ============================================================================
# 10. Estatísticas
# ============================================================================
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                  📊 ESTATÍSTICAS DO BUILD                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

if command -v du &> /dev/null; then
    BUILD_SIZE=$(du -sh "$DEPLOY_DIR" 2>/dev/null | cut -f1)
    echo "Tamanho do pacote: $BUILD_SIZE"
    
    FILE_COUNT=$(find "$DEPLOY_DIR" -type f | wc -l)
    echo "Total de arquivos: $FILE_COUNT"
fi

echo ""

# ============================================================================
# RESUMO
# ============================================================================
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                  ✅ PREPARAÇÃO COMPLETA!                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📁 Pacote pronto em: $DEPLOY_DIR/"
echo ""
echo "📝 Próximos passos:"
echo "   1. Leia: $DEPLOY_DIR/INSTRUCOES_UPLOAD.txt"
echo "   2. Acesse File Manager do Hostinger"
echo "   3. Faça upload dos arquivos de $DEPLOY_DIR/"
echo "   4. Configure SSL no painel Hostinger"
echo "   5. Acesse seu site: https://seudominio.com"
echo ""
echo "🔧 Backend deve estar rodando em:"
echo "   $BACKEND_URL"
echo ""
echo "📖 Documentação completa: DEPLOY_HOSTINGER_SHARED.md"
echo ""
log_info "Tudo pronto para deploy! 🚀"
echo ""
