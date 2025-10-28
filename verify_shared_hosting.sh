#!/bin/bash
# ============================================================================
# AudioMedic - Verificação de Deploy em Hospedagem Compartilhada
# ============================================================================

set -e

echo "=================================================="
echo "  AudioMedic - Verificação de Deploy"
echo "=================================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Ask for URLs
echo "Digite a URL do backend (ex: https://audiomedic-backend.onrender.com):"
read BACKEND_URL

echo "Digite a URL do frontend (ex: https://seudominio.com):"
read FRONTEND_URL

echo ""
echo "=================================================="
echo "  Testando Backend"
echo "=================================================="
echo ""

# Test backend health
echo "1. Testando endpoint raiz do backend..."
BACKEND_RESPONSE=$(curl -s -w "\n%{http_code}" "${BACKEND_URL}/api/" || echo "000")
BACKEND_CODE=$(echo "$BACKEND_RESPONSE" | tail -n1)
BACKEND_BODY=$(echo "$BACKEND_RESPONSE" | head -n-1)

if [ "$BACKEND_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Backend respondendo (HTTP $BACKEND_CODE)${NC}"
    echo "   Resposta: $BACKEND_BODY"
else
    echo -e "${RED}❌ Backend não responde (HTTP $BACKEND_CODE)${NC}"
    echo "   Verifique se o serviço está rodando no Render"
fi

echo ""
echo "2. Testando CORS..."
CORS_RESPONSE=$(curl -s -H "Origin: ${FRONTEND_URL}" -H "Access-Control-Request-Method: POST" -X OPTIONS "${BACKEND_URL}/api/auth/login" -w "\n%{http_code}" || echo "000")
CORS_CODE=$(echo "$CORS_RESPONSE" | tail -n1)

if [ "$CORS_CODE" = "200" ] || [ "$CORS_CODE" = "204" ]; then
    echo -e "${GREEN}✅ CORS configurado corretamente${NC}"
else
    echo -e "${YELLOW}⚠️  CORS pode ter problemas (HTTP $CORS_CODE)${NC}"
    echo "   Verifique CORS_ORIGINS no Render inclui: $FRONTEND_URL"
fi

echo ""
echo "=================================================="
echo "  Testando Frontend"
echo "=================================================="
echo ""

echo "1. Testando acesso ao frontend..."
FRONTEND_RESPONSE=$(curl -s -w "\n%{http_code}" "${FRONTEND_URL}" || echo "000")
FRONTEND_CODE=$(echo "$FRONTEND_RESPONSE" | tail -n1)

if [ "$FRONTEND_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Frontend acessível (HTTP $FRONTEND_CODE)${NC}"
else
    echo -e "${RED}❌ Frontend não acessível (HTTP $FRONTEND_CODE)${NC}"
    echo "   Verifique o upload para public_html/ no Hostinger"
fi

echo ""
echo "2. Testando redirecionamento HTTPS..."
HTTP_RESPONSE=$(curl -s -w "\n%{http_code}" -L "http://${FRONTEND_URL#https://}" || echo "000")
HTTP_CODE=$(echo "$HTTP_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ HTTPS funcionando (HTTP $HTTP_CODE)${NC}"
else
    echo -e "${YELLOW}⚠️  Verifique configuração SSL/HTTPS${NC}"
fi

echo ""
echo "3. Verificando React Router (.htaccess)..."
ROUTE_RESPONSE=$(curl -s -w "\n%{http_code}" "${FRONTEND_URL}/dashboard" || echo "000")
ROUTE_CODE=$(echo "$ROUTE_RESPONSE" | tail -n1)

if [ "$ROUTE_CODE" = "200" ]; then
    echo -e "${GREEN}✅ React Router funcionando (.htaccess OK)${NC}"
else
    echo -e "${RED}❌ React Router não funciona (HTTP $ROUTE_CODE)${NC}"
    echo "   Verifique se .htaccess está em public_html/"
fi

echo ""
echo "=================================================="
echo "  Testando Integração"
echo "=================================================="
echo ""

echo "1. Testando endpoint de registro..."
REG_RESPONSE=$(curl -s -X POST "${BACKEND_URL}/api/auth/register" \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"TestPassword123!","name":"Test"}' \
    -w "\n%{http_code}" || echo "000")
REG_CODE=$(echo "$REG_RESPONSE" | tail -n1)

if [ "$REG_CODE" = "200" ] || [ "$REG_CODE" = "400" ]; then
    echo -e "${GREEN}✅ Endpoint de registro funcional (HTTP $REG_CODE)${NC}"
    if [ "$REG_CODE" = "400" ]; then
        echo "   (400 esperado se usuário já existe)"
    fi
else
    echo -e "${YELLOW}⚠️  Endpoint pode ter problemas (HTTP $REG_CODE)${NC}"
fi

echo ""
echo "=================================================="
echo "  Resumo"
echo "=================================================="
echo ""

ALL_OK=true

if [ "$BACKEND_CODE" != "200" ]; then
    echo -e "${RED}❌ Backend não está respondendo${NC}"
    ALL_OK=false
fi

if [ "$FRONTEND_CODE" != "200" ]; then
    echo -e "${RED}❌ Frontend não está acessível${NC}"
    ALL_OK=false
fi

if [ "$ROUTE_CODE" != "200" ]; then
    echo -e "${RED}❌ React Router (.htaccess) não funciona${NC}"
    ALL_OK=false
fi

if [ "$ALL_OK" = true ]; then
    echo -e "${GREEN}🎉 Todos os testes passaram! Sistema funcionando.${NC}"
    echo ""
    echo "Próximos passos:"
    echo "1. Criar usuário admin: Execute create_admin.py no Render"
    echo "2. Testar login no frontend"
    echo "3. Criar transcrição de teste"
    echo "4. Configurar UptimeRobot (manter backend ativo)"
else
    echo -e "${RED}⚠️  Alguns testes falharam. Verifique os problemas acima.${NC}"
fi

echo ""
echo "=================================================="
