# 🎙️ AudioMedic - Sistema de Transcrição Médica Inteligente

Sistema completo de transcrição de consultas médicas com IA, estruturação automática de prontuários e segurança de nível empresarial.

---

## 📋 Características

### 🎯 Funcionalidades Principais
- ✅ **Gravação de Áudio** - Captura via navegador
- ✅ **Transcrição Automática** - OpenAI Whisper (português)
- ✅ **Estruturação Clínica** - GPT-5 organiza em seções
- ✅ **Gestão Completa** - CRUD de transcrições
- ✅ **Exportação** - Download de prontuários
- ✅ **Dashboard Admin** - Gestão de usuários

### 🔐 Segurança
- ✅ Senha forte validada (8+ chars, complexidade)
- ✅ Bcrypt cost 12
- ✅ Rate limiting por endpoint
- ✅ Brute force protection (5 tentativas)
- ✅ 8 Headers de segurança (HSTS, CSP, etc)
- ✅ Verificação de email
- ✅ Recuperação de senha
- ✅ MFA/TOTP para admins

### 💼 Sistema de Assinaturas
- Trial 14 dias
- Período de graça 7 dias
- Modo leitura pós-expiração
- Gestão admin de renovações

---

## 🚀 Deploy no Hostinger

### Guia Rápido
```bash
# 1. Copiar arquivos para servidor
scp -r . root@seu-ip:/var/www/audiomedic/

# 2. Executar script de deploy
ssh root@seu-ip
cd /var/www/audiomedic
chmod +x deploy_hostinger.sh
./deploy_hostinger.sh

# 3. Criar admin
cd backend
source venv/bin/activate
python3 create_admin.py
```

### Documentação Completa
📖 **Ver:** `DEPLOY_HOSTINGER.md` para instruções detalhadas

---

## 🛠️ Tecnologias

**Backend:** FastAPI, MongoDB, OpenAI, JWT, Bcrypt  
**Frontend:** React, Tailwind CSS, Shadcn/UI  
**DevOps:** Nginx, Supervisor, Let's Encrypt  

---

## 📚 Documentação

- **Deploy:** `DEPLOY_HOSTINGER.md`
- **Segurança:** `SECURITY_DOCUMENTATION.md`
- **API:** Swagger em `/api/docs` (dev only)

---

## 🔑 Configuração Mínima

**Backend (.env):**
```bash
MONGO_URL=mongodb+srv://...
OPENAI_API_KEY=sk-...
JWT_SECRET=...
FRONTEND_URL=https://seudominio.com
```

**Frontend (.env.production):**
```bash
REACT_APP_BACKEND_URL=https://seudominio.com
```

---

## 📊 Status

- **Versão:** 2.0.0
- **Testes:** 18/18 ✅
- **Status:** Produção Ready

---

**Desenvolvido para profissionais da saúde 🏥**
