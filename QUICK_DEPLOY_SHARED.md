# 🚀 AudioMedic - Quick Deploy (Hospedagem Compartilhada)

## TL;DR - Deploy em 3 Passos

### 1. Backend no Render (5 min)
```bash
cd backend
git init
git add .
git commit -m "Initial commit"
# Push para GitHub e conectar no Render
# Configurar variáveis de ambiente no dashboard
```

### 2. Frontend no Hostinger (5 min)
```bash
cd frontend
cp .env.production.example .env.production
# Editar .env.production com URL do backend
./build_production.sh
# Upload build/* para public_html/ via FTP
```

### 3. Criar Admin (2 min)
```bash
# No Render Dashboard → Shell
python3 create_admin.py
```

---

## 📚 Documentação Completa

- **Deploy Completo:** [`DEPLOY_HOSTINGER_SHARED.md`](DEPLOY_HOSTINGER_SHARED.md)
- **Checklist Rápido:** [`DEPLOY_CHECKLIST_SHARED.md`](DEPLOY_CHECKLIST_SHARED.md)
- **Segurança:** [`backend/SECURITY_DOCUMENTATION.md`](backend/SECURITY_DOCUMENTATION.md)

---

## ⚙️ Configuração Rápida

### MongoDB Atlas (Gratuito)
1. https://mongodb.com/cloud/atlas
2. Criar cluster M0 (512MB grátis)
3. Criar usuário e permitir acesso de anywhere (0.0.0.0/0)
4. Copiar connection string

### Render (Gratuito)
1. https://render.com
2. Conectar repositório GitHub
3. Criar Web Service (detecta `render.yaml` automaticamente)
4. Configurar variáveis:
   - MONGO_URL: `sua-connection-string`
   - OPENAI_API_KEY: `sua-chave` (ou EMERGENT_LLM_KEY)
   - FRONTEND_URL: `https://seudominio.com`
   - CORS_ORIGINS: `https://seudominio.com`

### Hostinger
1. Login no painel
2. File Manager → public_html/
3. Deletar arquivos padrão
4. Upload de `frontend/build/*`
5. Upload de `frontend/.htaccess`

---

## 🧪 Verificação

```bash
# Testar backend
curl https://SEU-BACKEND.onrender.com/api/

# Testar frontend
curl https://seudominio.com

# Verificação completa
./verify_shared_hosting.sh
```

---

## 🆘 Suporte

### Backend não responde
- Verifique logs: Render Dashboard → Logs
- Verifique variáveis de ambiente
- Backend "dorme" após 15 min: use UptimeRobot

### Frontend não carrega
- Verifique arquivos em `/public_html/`
- Verifique `.htaccess` presente
- Limpe cache do navegador

### CORS Error
- CORS_ORIGINS deve incluir seu domínio frontend
- Rebuild frontend se mudou REACT_APP_BACKEND_URL

---

## 📋 Novidades Versão 2.0

### ❌ Removido Trial Gratuito
- Novos usuários não recebem período de teste
- Admin deve ativar assinatura manualmente
- Usuários sem assinatura: acesso bloqueado

### 🔐 MFA Obrigatório para Admins
- Admin tem 7 dias para configurar MFA
- Após 7 dias: operações críticas bloqueadas
- Setup: Dashboard → Segurança → Configurar MFA

---

## 💰 Custos

| Serviço | Plano | Custo |
|---------|-------|-------|
| MongoDB Atlas | M0 | Grátis |
| Render | Free | Grátis* |
| Hostinger | Shared | Já contratado |

*Render Free: Backend "dorme" após inatividade. Use UptimeRobot para manter ativo.

---

## 🎉 Pronto!

Seu AudioMedic está online em hospedagem compartilhada! 🚀

**Acesse:** https://seudominio.com
