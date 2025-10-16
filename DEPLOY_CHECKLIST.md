# ✅ Checklist de Deploy - AudioMedic no Hostinger

## 📋 Pré-Deploy

### 1. Preparação Local
- [ ] Código testado e funcionando localmente
- [ ] Dependências atualizadas (requirements.txt, package.json)
- [ ] Variáveis de ambiente documentadas
- [ ] README.md atualizado
- [ ] Scripts de deploy testados

### 2. Credenciais Necessárias
- [ ] MongoDB Connection String (MongoDB Atlas ou local)
- [ ] OpenAI API Key (para Whisper)
- [ ] Emergent LLM Key (para GPT-5)
- [ ] JWT Secret (gerado automaticamente)
- [ ] SMTP Credentials (opcional, para emails)
- [ ] Domínio registrado e apontando para IP do servidor

### 3. Servidor Hostinger
- [ ] VPS contratado (mínimo VPS 1)
- [ ] Acesso SSH configurado
- [ ] IP público disponível
- [ ] Domínio configurado (DNS apontando para IP)

---

## 🚀 Deploy

### 1. Upload de Arquivos
```bash
# Via SCP
scp -r /caminho/local/audiomedic root@IP_SERVIDOR:/var/www/

# Ou via Git (se tiver repositório)
git clone https://github.com/seu-usuario/audiomedic.git /var/www/audiomedic
```
- [ ] Arquivos copiados para `/var/www/audiomedic`
- [ ] Permissões verificadas

### 2. Executar Script de Deploy
```bash
ssh root@IP_SERVIDOR
cd /var/www/audiomedic
chmod +x deploy_hostinger.sh
./deploy_hostinger.sh
```
- [ ] Script executado sem erros
- [ ] Python 3.11 instalado
- [ ] Node.js 18 instalado
- [ ] MongoDB configurado
- [ ] Dependências instaladas (backend)
- [ ] Frontend build gerado
- [ ] Supervisor configurado
- [ ] Nginx configurado
- [ ] Firewall ativado (UFW)

### 3. Configurar Variáveis de Ambiente
```bash
cd /var/www/audiomedic/backend
nano .env
```
- [ ] MONGO_URL configurado
- [ ] OPENAI_API_KEY adicionado
- [ ] EMERGENT_LLM_KEY adicionado
- [ ] JWT_SECRET gerado
- [ ] SMTP configurado (opcional)
- [ ] FRONTEND_URL com domínio correto
- [ ] CORS_ORIGINS configurado

```bash
cd /var/www/audiomedic/frontend
nano .env.production
```
- [ ] REACT_APP_BACKEND_URL com domínio correto

### 4. SSL/HTTPS
```bash
certbot --nginx -d seudominio.com -d www.seudominio.com
```
- [ ] Certbot instalado
- [ ] Certificado SSL obtido
- [ ] HTTPS funcionando
- [ ] Renovação automática configurada

### 5. Criar Usuário Admin
```bash
cd /var/www/audiomedic/backend
source venv/bin/activate
python3 create_admin.py
```
- [ ] Admin criado
- [ ] Credenciais guardadas em local seguro
- [ ] Login testado

---

## ✅ Pós-Deploy

### 1. Verificar Serviços
```bash
# Backend
supervisorctl status audiomedic-backend

# Nginx
systemctl status nginx

# Logs
tail -f /var/log/audiomedic/backend.err.log
```
- [ ] Backend rodando
- [ ] Nginx rodando
- [ ] Sem erros nos logs

### 2. Testes Funcionais

#### Frontend
- [ ] Acessar https://seudominio.com
- [ ] Landing page carrega
- [ ] Botões funcionam
- [ ] Design correto

#### Autenticação
- [ ] Registrar novo usuário
- [ ] Login funciona
- [ ] JWT token gerado
- [ ] Proteção de rotas funciona

#### Transcrições
- [ ] Gravar áudio
- [ ] Upload funciona
- [ ] Transcrição gerada (Whisper)
- [ ] Estruturação funciona (GPT-5)
- [ ] Exportar funciona

#### Admin
- [ ] Acessar painel admin
- [ ] Listar usuários
- [ ] Renovar assinatura
- [ ] Toggle status admin

#### Segurança
- [ ] Senha fraca rejeitada
- [ ] Brute force bloqueia após 5 tentativas
- [ ] Rate limiting funciona
- [ ] Headers de segurança presentes
- [ ] HTTPS forçado (redirect HTTP → HTTPS)

#### Emails (se SMTP configurado)
- [ ] Verificação de email enviado
- [ ] Reset de senha enviado
- [ ] MFA setup email enviado

### 3. Performance
```bash
# Testar carga
ab -n 100 -c 10 https://seudominio.com/api/
```
- [ ] Tempo de resposta < 500ms
- [ ] Servidor aguenta carga
- [ ] Memória estável

### 4. Monitoramento
```bash
# Configurar alertas (opcional)
# Instalar monitor (Netdata, Prometheus, etc)
```
- [ ] Logs configurados
- [ ] Alertas de erro configurados (opcional)
- [ ] Backup automático configurado (opcional)

---

## 📊 Endpoints Críticos

Testar cada um:

### Health Check
```bash
curl https://seudominio.com/api/
# Espera: {"message":"AudioMedic API","status":"running"}
```
- [ ] ✅ Funcionando

### Registro
```bash
curl -X POST https://seudominio.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"teste@teste.com","password":"TesteForte123!","name":"Teste"}'
```
- [ ] ✅ Funcionando

### Login
```bash
curl -X POST https://seudominio.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@seudominio.com","password":"SuaSenha123!"}'
```
- [ ] ✅ Funcionando

### Password Reset
```bash
curl -X POST https://seudominio.com/api/auth/request-password-reset \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@seudominio.com"}'
```
- [ ] ✅ Funcionando

---

## 🔐 Segurança Final

### Verificações Obrigatórias
- [ ] SSH keys configuradas (desabilitar password auth)
- [ ] Firewall ativo (UFW ou iptables)
- [ ] MongoDB protegido (IP whitelist ou VPN)
- [ ] Senhas fortes em todos os usuários
- [ ] JWT_SECRET único e seguro (64+ chars)
- [ ] SMTP password seguro
- [ ] Backup configurado
- [ ] Logs de auditoria ativos
- [ ] Rate limiting testado
- [ ] CORS restrito ao domínio correto
- [ ] SSL/TLS 1.2+ apenas
- [ ] Headers de segurança presentes (verificar com securityheaders.com)

### Ferramentas de Teste
```bash
# Teste SSL
https://www.ssllabs.com/ssltest/analyze.html?d=seudominio.com

# Teste Headers
https://securityheaders.com/?q=seudominio.com

# Teste Performance
https://pagespeed.web.dev/?url=seudominio.com
```
- [ ] SSL Rating A ou superior
- [ ] Headers Rating A
- [ ] Performance > 80

---

## 📝 Documentação

### Arquivos a Manter Atualizados
- [ ] README.md
- [ ] DEPLOY_HOSTINGER.md
- [ ] SECURITY_DOCUMENTATION.md
- [ ] .env.example (sem credenciais reais)
- [ ] requirements.txt
- [ ] package.json

### Credenciais a Guardar
- [ ] MongoDB connection string
- [ ] OpenAI API key
- [ ] Emergent LLM key
- [ ] SMTP password
- [ ] SSH keys
- [ ] Admin credentials
- [ ] JWT secret
- [ ] SSL certificates (backup)

---

## 🆘 Troubleshooting

### Backend não inicia
```bash
tail -f /var/log/audiomedic/backend.err.log
cd /var/www/audiomedic/backend
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001
```

### Frontend não carrega
```bash
ls -la /var/www/audiomedic/frontend/build
cd /var/www/audiomedic/frontend
yarn build
nginx -t
systemctl restart nginx
```

### MongoDB não conecta
```bash
# Testar conexão
python3 -c "from pymongo import MongoClient; client = MongoClient('MONGO_URL'); print(client.server_info())"
```

### SSL não funciona
```bash
certbot certificates
certbot renew --dry-run
systemctl restart nginx
```

---

## 📅 Manutenção Regular

### Diariamente
- [ ] Verificar logs de erro
- [ ] Monitorar uso de recursos

### Semanalmente
- [ ] Backup do banco de dados
- [ ] Verificar certificado SSL
- [ ] Atualizar dependências (se necessário)

### Mensalmente
- [ ] Revisar logs de segurança
- [ ] Testar restore de backup
- [ ] Atualizar sistema operacional
- [ ] Renovar assinaturas expiradas

---

## ✅ Deploy Completo

Quando todos os itens acima estiverem marcados:

**🎉 Parabéns! Seu AudioMedic está em produção!**

---

**Data de Deploy:** ___/___/_____  
**Responsável:** _________________  
**Domínio:** _____________________  
**IP Servidor:** _________________  
