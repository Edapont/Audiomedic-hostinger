#!/bin/bash

# ============================================================================
# AudioMedic - Script de Verificação Pré-Deploy
# ============================================================================

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║      🔍 AudioMedic - Verificação Pré-Deploy                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "${RED}✗${NC} $1 - AUSENTE"
        ((ERRORS++))
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1/"
        return 0
    else
        echo -e "${RED}✗${NC} $1/ - AUSENTE"
        ((ERRORS++))
        return 1
    fi
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

# ============================================================================
# 1. Verificar Estrutura de Diretórios
# ============================================================================
echo "📁 Verificando estrutura de diretórios..."
echo ""

check_dir "backend"
check_dir "frontend"
check_dir "frontend/src"
check_dir "frontend/src/pages"
check_dir "frontend/src/components/ui"
check_dir "frontend/public"

echo ""

# ============================================================================
# 2. Verificar Arquivos do Backend
# ============================================================================
echo "🐍 Verificando arquivos do Backend..."
echo ""

check_file "backend/server.py"
check_file "backend/security_utils.py"
check_file "backend/security_middleware.py"
check_file "backend/email_utils.py"
check_file "backend/requirements.txt"
check_file "backend/create_admin.py"
check_file "backend/test_security.py"
check_file "backend/.env.example"

if [ ! -f "backend/.env" ]; then
    warn "backend/.env não existe - crie a partir do .env.example"
fi

echo ""

# ============================================================================
# 3. Verificar Arquivos do Frontend
# ============================================================================
echo "⚛️  Verificando arquivos do Frontend..."
echo ""

check_file "frontend/package.json"
check_file "frontend/src/App.js"
check_file "frontend/src/App.css"
check_file "frontend/src/index.js"
check_file "frontend/src/pages/Landing.js"
check_file "frontend/src/pages/Auth.js"
check_file "frontend/src/pages/Dashboard.js"
check_file "frontend/src/pages/Recorder.js"
check_file "frontend/src/pages/TranscriptionDetail.js"
check_file "frontend/src/pages/AdminPanel.js"
check_file "frontend/.env.example"

if [ ! -f "frontend/.env.production" ]; then
    warn "frontend/.env.production não existe - crie a partir do .env.example"
fi

echo ""

# ============================================================================
# 4. Verificar Documentação
# ============================================================================
echo "📚 Verificando documentação..."
echo ""

check_file "README.md"
check_file "DEPLOY_HOSTINGER.md"
check_file "DEPLOY_CHECKLIST.md"
check_file "SECURITY_DOCUMENTATION.md"

echo ""

# ============================================================================
# 5. Verificar Scripts
# ============================================================================
echo "📜 Verificando scripts..."
echo ""

check_file "deploy_hostinger.sh"

if [ -f "deploy_hostinger.sh" ]; then
    if [ -x "deploy_hostinger.sh" ]; then
        echo -e "${GREEN}✓${NC} deploy_hostinger.sh é executável"
    else
        warn "deploy_hostinger.sh não é executável - execute: chmod +x deploy_hostinger.sh"
    fi
fi

if [ -f "backend/create_admin.py" ]; then
    if [ -x "backend/create_admin.py" ]; then
        echo -e "${GREEN}✓${NC} create_admin.py é executável"
    else
        warn "create_admin.py não é executável - execute: chmod +x backend/create_admin.py"
    fi
fi

echo ""

# ============================================================================
# 6. Verificar Sintaxe Python
# ============================================================================
echo "🐍 Verificando sintaxe Python..."
echo ""

if command -v python3 &> /dev/null; then
    for file in backend/*.py; do
        if [ -f "$file" ]; then
            if python3 -m py_compile "$file" 2>/dev/null; then
                echo -e "${GREEN}✓${NC} $file - sintaxe OK"
            else
                echo -e "${RED}✗${NC} $file - ERRO DE SINTAXE"
                ((ERRORS++))
            fi
        fi
    done
else
    warn "Python3 não encontrado - pulando verificação de sintaxe"
fi

echo ""

# ============================================================================
# 7. Verificar package.json
# ============================================================================
echo "📦 Verificando package.json..."
echo ""

if [ -f "frontend/package.json" ]; then
    if command -v jq &> /dev/null; then
        DEPENDENCIES=$(jq -r '.dependencies | keys[]' frontend/package.json 2>/dev/null | wc -l)
        echo -e "${GREEN}✓${NC} $DEPENDENCIES dependências listadas"
    else
        echo -e "${GREEN}✓${NC} package.json existe"
    fi
else
    echo -e "${RED}✗${NC} package.json não encontrado"
    ((ERRORS++))
fi

echo ""

# ============================================================================
# 8. Verificar requirements.txt
# ============================================================================
echo "📦 Verificando requirements.txt..."
echo ""

if [ -f "backend/requirements.txt" ]; then
    PACKAGES=$(grep -v "^#" backend/requirements.txt | grep -v "^$" | wc -l)
    echo -e "${GREEN}✓${NC} $PACKAGES pacotes listados"
    
    # Verificar pacotes críticos
    CRITICAL_PACKAGES=(
        "fastapi"
        "uvicorn"
        "motor"
        "bcrypt"
        "pyjwt"
        "slowapi"
        "emergentintegrations"
        "openai"
    )
    
    for pkg in "${CRITICAL_PACKAGES[@]}"; do
        if grep -qi "^$pkg" backend/requirements.txt; then
            echo -e "${GREEN}✓${NC} $pkg presente"
        else
            echo -e "${RED}✗${NC} $pkg AUSENTE"
            ((ERRORS++))
        fi
    done
else
    echo -e "${RED}✗${NC} requirements.txt não encontrado"
    ((ERRORS++))
fi

echo ""

# ============================================================================
# 9. Verificar .gitignore
# ============================================================================
echo "🔒 Verificando .gitignore..."
echo ""

if [ -f ".gitignore" ]; then
    if grep -q ".env" .gitignore; then
        echo -e "${GREEN}✓${NC} .env está no .gitignore"
    else
        warn ".env não está no .gitignore - ADICIONE PARA NÃO COMMITAR CREDENCIAIS"
    fi
    
    if grep -q "node_modules" .gitignore; then
        echo -e "${GREEN}✓${NC} node_modules está no .gitignore"
    else
        warn "node_modules deveria estar no .gitignore"
    fi
    
    if grep -q "venv" .gitignore; then
        echo -e "${GREEN}✓${NC} venv está no .gitignore"
    else
        warn "venv deveria estar no .gitignore"
    fi
else
    warn ".gitignore não encontrado - crie um para evitar commitar arquivos sensíveis"
fi

echo ""

# ============================================================================
# 10. Tamanho do Projeto
# ============================================================================
echo "📊 Tamanho do projeto..."
echo ""

if command -v du &> /dev/null; then
    BACKEND_SIZE=$(du -sh backend 2>/dev/null | cut -f1)
    FRONTEND_SIZE=$(du -sh frontend 2>/dev/null | cut -f1)
    TOTAL_SIZE=$(du -sh . 2>/dev/null | cut -f1)
    
    echo "Backend:  $BACKEND_SIZE"
    echo "Frontend: $FRONTEND_SIZE"
    echo "Total:    $TOTAL_SIZE"
fi

echo ""

# ============================================================================
# RESUMO
# ============================================================================
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    📊 RESUMO DA VERIFICAÇÃO                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ Perfeito! Nenhum erro ou aviso encontrado.${NC}"
    echo ""
    echo "Seu projeto está pronto para deploy! 🚀"
    echo ""
    echo "Próximos passos:"
    echo "  1. Configure backend/.env com suas credenciais"
    echo "  2. Configure frontend/.env.production com seu domínio"
    echo "  3. Execute: ./deploy_hostinger.sh"
    echo ""
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  $WARNINGS aviso(s) encontrado(s)${NC}"
    echo ""
    echo "Projeto OK para deploy, mas revise os avisos acima."
    echo ""
    exit 0
else
    echo -e "${RED}❌ $ERRORS erro(s) encontrado(s)${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠️  $WARNINGS aviso(s) encontrado(s)${NC}"
    fi
    echo ""
    echo "Corrija os erros antes de fazer deploy!"
    echo ""
    exit 1
fi
