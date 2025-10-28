#!/bin/bash
# ============================================================================
# AudioMedic - Script de Build para Produção (Hostinger Shared)
# ============================================================================

set -e  # Exit on error

echo "=================================================="
echo "  AudioMedic - Build de Produção"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running from frontend directory
if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ Erro: Execute este script da pasta frontend${NC}"
    echo "   cd frontend && ./build_production.sh"
    exit 1
fi

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo -e "${YELLOW}⚠️  Arquivo .env.production não encontrado${NC}"
    echo ""
    
    if [ -f ".env.production.example" ]; then
        echo "Copiando .env.production.example para .env.production..."
        cp .env.production.example .env.production
        echo -e "${GREEN}✅ Arquivo criado!${NC}"
        echo ""
        echo -e "${YELLOW}IMPORTANTE: Edite .env.production e configure:${NC}"
        echo "  1. REACT_APP_BACKEND_URL com a URL do seu backend"
        echo ""
        echo "Pressione Enter após configurar..."
        read
    else
        echo -e "${RED}❌ Erro: .env.production.example não encontrado${NC}"
        exit 1
    fi
fi

echo "📋 Verificando configuração..."
echo ""

# Display backend URL
BACKEND_URL=$(grep REACT_APP_BACKEND_URL .env.production | cut -d '=' -f2)
echo "   Backend URL: ${BACKEND_URL}"

if [ "$BACKEND_URL" = "https://audiomedic-backend.onrender.com" ]; then
    echo -e "${YELLOW}   ⚠️  Usando URL de exemplo. Certifique-se de ajustar se necessário.${NC}"
fi

echo ""
echo "🧹 Limpando build anterior..."
rm -rf build/

echo ""
echo "📦 Instalando dependências..."
yarn install --frozen-lockfile

echo ""
echo "🔨 Gerando build de produção..."
yarn build

if [ ! -d "build" ]; then
    echo -e "${RED}❌ Erro: Build falhou - pasta build/ não foi criada${NC}"
    exit 1
fi

echo ""
echo "📊 Estatísticas do build:"
du -sh build/
echo "   Arquivos: $(find build -type f | wc -l)"

echo ""
echo "✅ Build concluído com sucesso!"
echo ""
echo "=================================================="
echo "  Próximos Passos"
echo "=================================================="
echo ""
echo "1. Teste local (opcional):"
echo "   npx serve -s build -p 5000"
echo ""
echo "2. Upload para Hostinger:"
echo "   - Via FTP: Upload do conteúdo de build/* para public_html/"
echo "   - Via File Manager: Upload dos arquivos para public_html/"
echo ""
echo "3. Certifique-se de copiar .htaccess para public_html/"
echo "   cp .htaccess build/.htaccess (se ainda não estiver)"
echo ""
echo "4. Verifique se o site está funcionando:"
echo "   https://seudominio.com"
echo ""
echo "=================================================="
