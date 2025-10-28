# ✅ Checklist Rápido - Deploy Hospedagem Compartilhada

## 📋 Pré-requisitos
- [ ] Conta Hostinger (hospedagem compartilhada)
- [ ] Conta Render.com (gratuita)
- [ ] Conta MongoDB Atlas (gratuita)
- [ ] Conta GitHub (para deploy backend)

---

## 🗄️ MongoDB Atlas
- [ ] Cluster M0 criado
- [ ] Usuário do banco criado
- [ ] Network Access: 0.0.0.0/0 (anywhere)
- [ ] Connection string copiado

---

## 🔧 Backend (Render)
- [ ] Repositório GitHub criado (audiomedic-backend)
- [ ] Código do backend commitado e pushed
- [ ] Arquivo `render.yaml` presente
- [ ] Web Service criado no Render
- [ ] Variáveis de ambiente configuradas:
  - [ ] MONGO_URL
  - [ ] OPENAI_API_KEY (ou EMERGENT_LLM_KEY)
  - [ ] FRONTEND_URL
  - [ ] CORS_ORIGINS
- [ ] Deploy concluído (status: Live)
- [ ] Endpoint testado: `curl https://SEU-BACKEND.onrender.com/api/`
- [ ] Resposta esperada: `{"message":"AudioMedic API","status":"running"}`

---

## 🎨 Frontend (Hostinger)
- [ ] Arquivo `.env.production` criado e configurado
- [ ] REACT_APP_BACKEND_URL apontando para Render
- [ ] Build gerado: `cd frontend && ./build_production.sh`
- [ ] Pasta `build/` criada com sucesso
- [ ] Conteúdo de `build/*` uploadado para `/public_html/` via FTP ou File Manager
- [ ] Arquivo `.htaccess` presente em `/public_html/`
- [ ] Site acessível: https://seudominio.com

---

## 👤 Criar Admin
- [ ] Acessar Render Dashboard → Shell
- [ ] Executar: `python3 create_admin.py`
- [ ] Credenciais guardadas

---

## ✅ Testes Funcionais

### Frontend
- [ ] Landing page carrega
- [ ] Botão "Começar Agora" funciona
- [ ] Navegação entre páginas funciona

### Autenticação
- [ ] Login funciona
- [ ] Usuário não pode acessar recursos sem assinatura
- [ ] Admin tem acesso total

### Transcrição (Admin)
- [ ] Gravar áudio
- [ ] Upload funciona
- [ ] Transcrição gerada
- [ ] Estruturação funciona
- [ ] Exportar funciona

### Admin Panel
- [ ] Listar usuários
- [ ] Renovar assinatura de usuário
- [ ] Configurar MFA (obrigatório após 7 dias)

### Segurança
- [ ] HTTPS ativo (redirect HTTP → HTTPS)
- [ ] Senha fraca rejeitada
- [ ] Rate limiting funciona

---

## 🔐 Segurança Final
- [ ] SSL/HTTPS ativo no Hostinger
- [ ] CORS configurado corretamente
- [ ] JWT_SECRET único gerado
- [ ] MFA configurado para admin principal

---

## 🔄 Manutenção (Opcional)
- [ ] UptimeRobot configurado (manter backend ativo)
  - URL: https://uptimerobot.com/
  - Monitor: https://SEU-BACKEND.onrender.com/api/
  - Intervalo: 5 minutos
- [ ] Backup MongoDB Atlas configurado

---

## 📊 Verificação Automática
Execute o script de verificação:
```bash
./verify_shared_hosting.sh
```

---

## ⚠️ Limitações Conhecidas

### Render Free Tier
- ❌ Backend "dorme" após 15 min de inatividade
- ❌ Primeira requisição após "sono" demora ~30s
- ✅ 750h/mês disponíveis (mais do que suficiente)
- 💡 Solução: UptimeRobot (fazer ping a cada 5 min)

### Hostinger Compartilhado
- ✅ Perfeito para React build estático
- ✅ SSL/HTTPS incluído
- ❌ Não roda Python/FastAPI (por isso backend no Render)

---

## 🆘 Problemas Comuns

### Backend não responde
1. Verificar logs no Render Dashboard
2. Verificar se variáveis de ambiente estão corretas
3. Testar MongoDB connection string

### Frontend não carrega
1. Verificar se arquivos estão em `/public_html/`
2. Verificar se `.htaccess` está presente
3. Limpar cache do navegador

### CORS Error
1. Verificar `CORS_ORIGINS` no Render inclui seu domínio
2. Verificar `REACT_APP_BACKEND_URL` no build frontend
3. Rebuild frontend após alterar variáveis

### "Assinatura expirada" ao registrar
⚠️ **ESPERADO**: Novo design sem trial gratuito
- Admin deve ativar assinatura manualmente no painel
- Usuários sem assinatura ativa não podem criar transcrições

### Admin bloqueado por MFA
⚠️ **ESPERADO**: MFA obrigatório após 7 dias
- Admin tem 7 dias de graça para configurar MFA
- Após 7 dias, operações críticas bloqueadas até configurar
- Setup: /auth/setup-mfa → Scan QR code → /auth/confirm-mfa

---

## 🎉 Deploy Completo!

Quando todos os itens estiverem marcados, seu AudioMedic está em produção! 🚀

**Frontend:** https://seudominio.com  
**Backend:** https://SEU-BACKEND.onrender.com  
**Database:** MongoDB Atlas

---

**Última Atualização:** Deploy para Hospedagem Compartilhada  
**Versão:** 2.0-secure (sem trial, MFA obrigatório para admins)
