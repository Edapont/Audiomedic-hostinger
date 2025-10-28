# 🔄 Migração: Hospedagem Compartilhada → VPS Privado

## ✅ Você Agora Tem VPS!

Com um VPS do Hostinger, você pode rodar **tudo no mesmo servidor**:
- ✅ Backend FastAPI (Python)
- ✅ Frontend React
- ✅ MongoDB (opcional - pode usar Atlas)
- ✅ Supervisor para gerenciar processos
- ✅ Nginx como proxy reverso

---

## 🎯 Diferenças: Compartilhado vs VPS

| Aspecto | Hospedagem Compartilhada | VPS Privado |
|---------|-------------------------|-------------|
| Backend | ❌ Render.com (externo) | ✅ No próprio servidor |
| Frontend | ✅ public_html/ | ✅ Nginx servindo build/ |
| MongoDB | MongoDB Atlas | Atlas OU local no VPS |
| Supervisor | ❌ Não disponível | ✅ Gerencia processos |
| Nginx | ❌ Apache limitado | ✅ Nginx completo |
| SSL | ✅ Incluído | ✅ Certbot (Let's Encrypt) |
| Custo | Incluído + Grátis | Tudo incluído no VPS |

---

## 🚀 Guia Rápido de Deploy no VPS

### 📚 Documentação Completa
👉 **Siga o guia completo em:** [`DEPLOY_HOSTINGER.md`](DEPLOY_HOSTINGER.md)

### ⚡ Versão TL;DR (3 Passos)

#### 1️⃣ Preparar VPS
```bash
ssh root@SEU-IP-HOSTINGER

# Executar script de deploy automático
cd /var/www/audiomedic
chmod +x deploy_hostinger.sh
./deploy_hostinger.sh
```

#### 2️⃣ Configurar Variáveis de Ambiente

**Backend (.env):**
```bash
cd /var/www/audiomedic/backend
nano .env
```

Configurar:
```env
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/audiomedic_db
JWT_SECRET=<gerar-secret-forte>
OPENAI_API_KEY=sk-...
FRONTEND_URL=https://seudominio.com
CORS_ORIGINS=https://seudominio.com,https://www.seudominio.com
```

**Frontend (.env.production):**
```bash
cd /var/www/audiomedic/frontend
nano .env.production
```

Configurar:
```env
REACT_APP_BACKEND_URL=https://seudominio.com
```

#### 3️⃣ SSL e Testar
```bash
# Instalar SSL
certbot --nginx -d seudominio.com -d www.seudominio.com

# Reiniciar serviços
supervisorctl restart all
systemctl restart nginx

# Testar
curl https://seudominio.com/api/
```

---

## 📝 Checklist de Migração

### Pré-Deploy
- [ ] VPS Hostinger contratado
- [ ] Acesso SSH configurado
- [ ] Domínio apontando para IP do VPS
- [ ] MongoDB Atlas criado (ou planeja instalar local)
- [ ] Credenciais API (OpenAI ou Emergent LLM Key)

### Durante Deploy
- [ ] Dependências instaladas (Python, Node, Nginx, Supervisor)
- [ ] Projeto clonado/uploadado para `/var/www/audiomedic`
- [ ] Backend configurado (venv, .env, requirements.txt)
- [ ] Frontend buildado (yarn build)
- [ ] Supervisor configurado
- [ ] Nginx configurado
- [ ] SSL instalado (Certbot)
- [ ] Firewall configurado (UFW)

### Pós-Deploy
- [ ] Admin criado (`python3 create_admin.py`)
- [ ] Backend respondendo: `curl https://seudominio.com/api/`
- [ ] Frontend carregando: `https://seudominio.com`
- [ ] Login funcionando
- [ ] Transcrição de teste criada
- [ ] MFA configurado para admin (7 dias)

---

## 🔧 Comandos Úteis VPS

### Gerenciar Serviços
```bash
# Status de todos os serviços
supervisorctl status

# Reiniciar backend
supervisorctl restart audiomedic-backend

# Reiniciar frontend (build novo)
cd /var/www/audiomedic/frontend
yarn build
systemctl restart nginx

# Ver logs
tail -f /var/log/audiomedic/backend.err.log
tail -f /var/log/nginx/error.log
```

### Verificar Recursos
```bash
# Uso de disco
df -h

# Uso de memória
free -h

# Processos Python
ps aux | grep python

# Portas em uso
netstat -tulpn | grep LISTEN
```

### Backup
```bash
# Backup manual do banco (se MongoDB local)
mongodump --out /backup/audiomedic-$(date +%Y%m%d)

# Backup do código
tar -czf /backup/audiomedic-code-$(date +%Y%m%d).tar.gz /var/www/audiomedic
```

---

## ⚠️ Arquivos Que NÃO São Mais Necessários

Com VPS, você **não precisa mais** destes arquivos (criados para hospedagem compartilhada):

- ❌ `backend/render.yaml` - Era para deploy no Render
- ❌ `DEPLOY_HOSTINGER_SHARED.md` - Era para compartilhada
- ❌ `DEPLOY_CHECKLIST_SHARED.md` - Era para compartilhada
- ❌ `QUICK_DEPLOY_SHARED.md` - Era para compartilhada
- ❌ `verify_shared_hosting.sh` - Era para testar compartilhada
- ❌ `frontend/.htaccess` - Era para Apache (no VPS usa Nginx)

**Mantenha:**
- ✅ `DEPLOY_HOSTINGER.md` - Guia completo para VPS
- ✅ `deploy_hostinger.sh` - Script de deploy VPS
- ✅ `DEPLOY_CHECKLIST.md` - Checklist VPS
- ✅ `backend/.env.example` - Template de variáveis
- ✅ `frontend/.env.production.example` - Template frontend

---

## 🆘 Problemas Comuns VPS

### Backend não inicia
```bash
# Ver logs detalhados
tail -n 100 /var/log/audiomedic/backend.err.log

# Testar manualmente
cd /var/www/audiomedic/backend
source venv/bin/activate
python3 -m uvicorn server:app --host 0.0.0.0 --port 8001
```

### Frontend não carrega
```bash
# Verificar build
ls -la /var/www/audiomedic/frontend/build/

# Testar Nginx
nginx -t
systemctl status nginx

# Rebuild
cd /var/www/audiomedic/frontend
yarn build
```

### Porta já em uso
```bash
# Ver o que está usando a porta 8001
lsof -i :8001

# Matar processo se necessário
kill -9 <PID>
```

---

## 📊 Comparação de Custos

### Hospedagem Compartilhada (Solução Antiga)
- Hostinger Compartilhado: R$ 10-30/mês
- Render Free Tier: Grátis (com limitações)
- MongoDB Atlas M0: Grátis
- **Total:** R$ 10-30/mês + backend "dormindo"

### VPS (Solução Nova)
- Hostinger VPS 1: R$ 30-50/mês
- MongoDB Atlas M0: Grátis (ou local)
- **Total:** R$ 30-50/mês + backend sempre ativo

**Vantagens do VPS:**
- ✅ Backend sempre ativo (sem "cold start")
- ✅ Mais recursos (CPU, RAM, disco)
- ✅ Controle total do servidor
- ✅ Possibilidade de MongoDB local
- ✅ Melhor performance

---

## 🎉 Próximo Passo

**Siga o guia completo:**
```bash
# Abra e siga o guia detalhado
cat DEPLOY_HOSTINGER.md
```

Ou use o **script automatizado:**
```bash
# No VPS, após clonar o projeto
cd /var/www/audiomedic
chmod +x deploy_hostinger.sh
./deploy_hostinger.sh
```

---

## 📞 Suporte

Se encontrar problemas durante o deploy:
1. Verifique logs: `tail -f /var/log/audiomedic/backend.err.log`
2. Teste componentes individualmente
3. Consulte `DEPLOY_HOSTINGER.md` para troubleshooting detalhado

**Boa sorte com seu VPS! 🚀**
