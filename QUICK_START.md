# 🚀 AudioMedic - Quick Start Guide

Deploy seu AudioMedic no Hostinger em **3 passos simples**!

---

## ⚡ Deploy Rápido (5 minutos)

### Passo 1: Preparar Arquivos Localmente

```bash
# 1. Verificar se tudo está OK
./verify_deploy.sh

# 2. Configurar variáveis (se ainda não fez)
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.production

# Editar os arquivos acima com suas credenciais
```

### Passo 2: Enviar para Servidor

```bash
# Substitua IP_SERVIDOR pelo IP do seu VPS Hostinger
scp -r /caminho/para/audiomedic root@IP_SERVIDOR:/var/www/
```

### Passo 3: Deploy Automático

```bash
# Conectar ao servidor
ssh root@IP_SERVIDOR

# Executar script de deploy
cd /var/www/audiomedic
./deploy_hostinger.sh

# Quando solicitado, informar seu domínio
# Exemplo: audiomedic.com

# Script fará TUDO automaticamente:
# - Instalar dependências
# - Configurar serviços
# - Gerar SSL
# - Iniciar aplicação
```

### Passo 4: Criar Admin

```bash
# Ainda conectado ao servidor
cd /var/www/audiomedic/backend
source venv/bin/activate
python3 create_admin.py

# Seguir instruções interativas
```

---

## ✅ Pronto!

Acesse: **https://seudominio.com**

---

## 🔑 Credenciais Necessárias

Antes de iniciar, tenha em mãos:

### Obrigatórias:
- [x] **MongoDB URL** (MongoDB Atlas gratuito: https://mongodb.com/cloud/atlas)
- [x] **OpenAI API Key** (https://platform.openai.com/api-keys)
- [x] **Domínio** registrado e apontando para IP do VPS

### Opcionais:
- [ ] **Emergent LLM Key** (se tiver)
- [ ] **SMTP Credentials** (Gmail, Hostinger Email, etc)

---

## 📋 Checklist Pré-Deploy

### Servidor Hostinger:
- [ ] VPS contratado (mínimo VPS 1)
- [ ] Acesso SSH funcionando
- [ ] Domínio apontando para IP

### Arquivos Locais:
- [ ] `backend/.env` configurado
- [ ] `frontend/.env.production` configurado
- [ ] `verify_deploy.sh` executado sem erros

---

## 🆘 Problemas Comuns

### "Permission denied" ao fazer SCP
```bash
# Solução: Usar sudo ou verificar permissões
sudo scp -r audiomedic root@IP:/var/www/
```

### "Python não encontrado"
```bash
# O script de deploy instala automaticamente
# Se der erro, execute manualmente:
apt install python3.11 python3.11-venv
```

### "MongoDB connection failed"
```bash
# Verificar se MONGO_URL está correto no .env
# Testar conexão:
python3 -c "from pymongo import MongoClient; client=MongoClient('SUA_URL'); print(client.server_info())"
```

### "SSL Certificate failed"
```bash
# Certifique-se que:
# 1. Domínio aponta para IP correto (DNS propagado)
# 2. Portas 80 e 443 abertas no firewall
# 3. Aguarde até 48h propagação DNS

# Tentar manualmente:
certbot --nginx -d seudominio.com
```

---

## 📖 Documentação Completa

- **Deploy Detalhado:** `DEPLOY_HOSTINGER.md`
- **Checklist Completo:** `DEPLOY_CHECKLIST.md`
- **Segurança:** `SECURITY_DOCUMENTATION.md`
- **README Geral:** `README.md`

---

## 🔄 Atualizar Aplicação

```bash
ssh root@IP_SERVIDOR
cd /var/www/audiomedic

# Pull changes (se usar git)
git pull

# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
supervisorctl restart audiomedic-backend

# Frontend
cd ../frontend
yarn install
yarn build
systemctl reload nginx
```

---

## 📊 Verificar Status

```bash
# Backend rodando?
supervisorctl status audiomedic-backend

# Nginx rodando?
systemctl status nginx

# Ver logs
tail -f /var/log/audiomedic/backend.err.log
```

---

## 🎯 Comandos Úteis

```bash
# Reiniciar backend
supervisorctl restart audiomedic-backend

# Reiniciar nginx
systemctl restart nginx

# Ver todos os logs
tail -f /var/log/audiomedic/*.log

# Testar API
curl https://seudominio.com/api/

# Criar novo admin
cd /var/www/audiomedic/backend
source venv/bin/activate
python3 create_admin.py
```

---

## 💡 Dicas

1. **Use MongoDB Atlas** (gratuito até 512MB)
2. **Configure SSL** no primeiro deploy
3. **Teste localmente** antes de fazer deploy
4. **Faça backup** do .env após configurar
5. **Monitore logs** nas primeiras 24h

---

## 🚀 Tempo Estimado

- **Preparação local:** 5 minutos
- **Upload arquivos:** 2 minutos
- **Deploy automático:** 10-15 minutos
- **Configuração final:** 5 minutos

**Total:** ~25-30 minutos para deploy completo

---

## ✅ Após Deploy

- [ ] Acessar https://seudominio.com
- [ ] Login como admin
- [ ] Criar transcrição de teste
- [ ] Verificar email (se configurado)
- [ ] Testar MFA (se admin)
- [ ] Configurar backup automático

---

**Dúvidas?** Consulte `DEPLOY_HOSTINGER.md` para guia detalhado!

🎉 **Boa sorte com seu deploy!**
