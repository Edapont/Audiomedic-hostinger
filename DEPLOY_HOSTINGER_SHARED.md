# 🏠 AudioMedic - Deploy em Hospedagem Compartilhada Hostinger

## ⚠️ Limitações da Hospedagem Compartilhada

Hospedagem compartilhada Hostinger **NÃO suporta**:
- ❌ Python 3.11 / FastAPI
- ❌ Processos em background (Supervisor)
- ❌ Acesso SSH root
- ❌ Instalação de serviços personalizados

## ✅ Solução: Arquitetura Híbrida

**Frontend:** Hospedagem Compartilhada Hostinger  
**Backend:** Render.com (Gratuito)  
**Banco:** MongoDB Atlas (Gratuito)

---

## 📋 Pré-requisitos

1. **Hostinger:** Plano compartilhado contratado
2. **Render.com:** Conta gratuita (criar em https://render.com)
3. **MongoDB Atlas:** Conta gratuita (criar em https://mongodb.com/cloud/atlas)
4. **GitHub:** Conta (para deploy do backend)

---

## 🚀 Passo 1: Configurar MongoDB Atlas

### 1.1 Criar Cluster
1. Acesse: https://mongodb.com/cloud/atlas
2. Registre-se gratuitamente
3. Clique em "Build a Database"
4. Escolha **M0 Free** (512MB grátis)
5. Escolha região próxima (ex: São Paulo)
6. Nome do cluster: `audiomedic-cluster`

### 1.2 Criar Usuário
1. Security → Database Access → Add New Database User
2. Username: `audiomedic_user`
3. Password: **gerar senha forte** (guardar!)
4. Database User Privileges: `Read and write to any database`
5. Add User

### 1.3 Permitir Acesso
1. Security → Network Access → Add IP Address
2. Selecionar: **Allow Access from Anywhere** (0.0.0.0/0)
3. Confirm

### 1.4 Obter Connection String
1. Database → Connect → Drivers
2. Copiar connection string:
```
mongodb+srv://audiomedic_user:<password>@audiomedic-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
```
3. Substituir `<password>` pela senha criada
4. **Guardar esse string!**

---

## 🚀 Passo 2: Deploy Backend no Render

### 2.1 Preparar Repositório GitHub

```bash
# 1. Criar repositório no GitHub (audiomedic-backend)

# 2. No seu computador local, preparar backend
cd /caminho/audiomedic
cd backend

# 3. Criar arquivo render.yaml
cat > render.yaml << 'EOF'
services:
  - type: web
    name: audiomedic-backend
    env: python
    region: oregon
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn server:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /api/
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: MONGO_URL
        sync: false
      - key: DB_NAME
        value: audiomedic_db
      - key: JWT_SECRET
        generateValue: true
      - key: JWT_ALGORITHM
        value: HS256
      - key: JWT_EXPIRATION_HOURS
        value: 24
      - key: EMERGENT_LLM_KEY
        sync: false
      - key: OPENAI_API_KEY
        sync: false
      - key: SMTP_HOST
        value: ""
      - key: SMTP_PORT
        value: 587
      - key: SMTP_USER
        value: ""
      - key: SMTP_PASSWORD
        value: ""
      - key: SMTP_FROM_EMAIL
        value: noreply@audiomedic.com
      - key: SMTP_FROM_NAME
        value: AudioMedic
      - key: SMTP_USE_TLS
        value: true
      - key: FRONTEND_URL
        sync: false
      - key: CORS_ORIGINS
        sync: false
EOF

# 4. Inicializar git (se ainda não fez)
git init
git add .
git commit -m "Initial commit - AudioMedic Backend"

# 5. Conectar ao GitHub
git remote add origin https://github.com/seu-usuario/audiomedic-backend.git
git branch -M main
git push -u origin main
```

### 2.2 Deploy no Render

1. Acesse: https://dashboard.render.com/
2. New → Web Service
3. Conectar ao seu repositório GitHub: `audiomedic-backend`
4. Render detectará automaticamente o `render.yaml`
5. Clique em **Create Web Service**

### 2.3 Configurar Variáveis de Ambiente

No painel do Render:

1. Ir em **Environment**
2. Adicionar/Editar as seguintes variáveis:

```
MONGO_URL = mongodb+srv://audiomedic_user:SUA_SENHA@audiomedic-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority

EMERGENT_LLM_KEY = sk-emergent-4154eD2D32b17E4A1C

OPENAI_API_KEY = sua_chave_openai_aqui

FRONTEND_URL = https://seudominio.com (ou https://seudominio.hostinger.com)

CORS_ORIGINS = https://seudominio.com,https://www.seudominio.com
```

3. Salvar e aguardar redeploy automático

### 2.4 Obter URL do Backend

Após deploy:
- URL será algo como: `https://audiomedic-backend.onrender.com`
- **Guardar essa URL!**
- Testar: `https://audiomedic-backend.onrender.com/api/`

---

## 🚀 Passo 3: Deploy Frontend no Hostinger

### 3.1 Preparar Build de Produção

No seu computador local:

```bash
cd /caminho/audiomedic/frontend

# 1. Configurar variáveis de ambiente
cat > .env.production << EOF
REACT_APP_BACKEND_URL=https://audiomedic-backend.onrender.com
REACT_APP_ENABLE_VISUAL_EDITS=false
ENABLE_HEALTH_CHECK=false
EOF

# 2. Instalar dependências (se não fez)
yarn install

# 3. Gerar build de produção
yarn build

# Resultado estará em: frontend/build/
```

### 3.2 Upload para Hostinger

**Opção A: Via File Manager (Web)**

1. Login no painel Hostinger: https://hpanel.hostinger.com/
2. File Manager → public_html
3. **Deletar** todos os arquivos padrão (index.html, etc)
4. Upload todos os arquivos da pasta `build/`
5. Estrutura final:
```
public_html/
├── index.html
├── static/
│   ├── css/
│   ├── js/
│   └── media/
├── manifest.json
├── favicon.ico
└── ...
```

**Opção B: Via FTP (Recomendado)**

1. Obter credenciais FTP no painel Hostinger
2. Usar FileZilla ou outro cliente FTP
3. Conectar ao servidor
4. Navegar até `/public_html/`
5. Deletar arquivos padrão
6. Upload pasta `build/*` para `/public_html/`

### 3.3 Configurar .htaccess

Criar arquivo `.htaccess` em `/public_html/`:

```bash
# No File Manager do Hostinger, criar arquivo .htaccess
```

Conteúdo do `.htaccess`:

```apache
# ============================================================================
# AudioMedic - Configuração Apache (Hostinger)
# ============================================================================

# Habilitar rewrite
RewriteEngine On

# Forçar HTTPS
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

# React Router - Direcionar todas as rotas para index.html
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule . /index.html [L]

# Headers de Segurança
<IfModule mod_headers.c>
    Header set X-Frame-Options "DENY"
    Header set X-Content-Type-Options "nosniff"
    Header set X-XSS-Protection "1; mode=block"
    Header set Referrer-Policy "strict-origin-when-cross-origin"
    Header set Permissions-Policy "geolocation=(), microphone=(), camera=()"
</IfModule>

# Compressão GZIP
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css text/javascript application/javascript application/json
</IfModule>

# Cache de arquivos estáticos
<IfModule mod_expires.c>
    ExpiresActive On
    ExpiresByType image/jpg "access plus 1 year"
    ExpiresByType image/jpeg "access plus 1 year"
    ExpiresByType image/png "access plus 1 year"
    ExpiresByType image/gif "access plus 1 year"
    ExpiresByType image/svg+xml "access plus 1 year"
    ExpiresByType text/css "access plus 1 month"
    ExpiresByType application/javascript "access plus 1 month"
    ExpiresByType application/json "access plus 1 week"
    ExpiresByType text/html "access plus 1 day"
</IfModule>

# Proteger arquivos sensíveis
<FilesMatch "(\.env|\.git|\.htaccess|\.htpasswd)">
    Order allow,deny
    Deny from all
</FilesMatch>
```

---

## 🚀 Passo 4: Criar Usuário Admin

### Via Render Dashboard

1. Acesse: https://dashboard.render.com/
2. Selecione seu serviço `audiomedic-backend`
3. Aba **Shell**
4. Execute:

```bash
python3 create_admin.py
```

5. Seguir instruções interativas
6. Guardar credenciais

---

## ✅ Passo 5: Testar Sistema

### 5.1 Testar Backend
```bash
curl https://audiomedic-backend.onrender.com/api/
# Esperado: {"message":"AudioMedic API","status":"running","version":"2.0-secure"}
```

### 5.2 Testar Frontend
1. Acessar: https://seudominio.com
2. Landing page deve carregar
3. Clicar em "Começar Agora"
4. Fazer login com credenciais admin
5. Criar transcrição de teste

---

## 🔧 Manutenção e Updates

### Atualizar Backend (Render)

```bash
# 1. Fazer mudanças no código
# 2. Commit e push
git add .
git commit -m "Update backend"
git push origin main

# 3. Render faz redeploy automático!
```

### Atualizar Frontend (Hostinger)

```bash
# 1. Fazer mudanças no código
cd frontend

# 2. Rebuild
yarn build

# 3. Upload novo build via FTP ou File Manager
# Sobrescrever arquivos em public_html/
```

---

## 💰 Custos

### Serviços Gratuitos:
- ✅ **MongoDB Atlas:** 512MB grátis (suficiente para começar)
- ✅ **Render.com:** 750h/mês grátis (mais do que suficiente)
- ✅ **Hostinger:** Já contratado

### ⚠️ Limitações do Plano Gratuito Render:
- Backend "dorme" após 15 min de inatividade
- Primeira requisição pode demorar ~30s para "acordar"
- **Solução:** Usar cron job para fazer ping a cada 10 min

### 🔄 Manter Backend Ativo (Opcional)

Usar serviço gratuito de uptime monitoring:
- UptimeRobot: https://uptimerobot.com/
- Configurar ping a cada 5 minutos para: `https://audiomedic-backend.onrender.com/api/`

---

## ⚠️ Limitações da Solução

### Render Free Tier:
- ❌ Backend "dorme" após inatividade
- ❌ Build pode falhar se demorar >15 min
- ✅ 750h/mês (mais do que suficiente)

### Hostinger Compartilhado:
- ❌ Não roda Python/FastAPI nativamente
- ✅ Perfeito para React build estático
- ✅ SSL/HTTPS incluído

### Alternativa Paga (se precisar):
- **Render Starter:** $7/mês (backend sempre ativo)
- **Railway Pro:** $5/mês (melhor performance)

---

## 🆘 Troubleshooting

### Backend não responde
```bash
# Verificar logs no Render Dashboard
# Aba "Logs" do serviço
```

### Frontend não carrega
1. Verificar se arquivos foram para `/public_html/`
2. Verificar `.htaccess` está presente
3. Verificar permissões (644 para arquivos, 755 para pastas)

### CORS Error
1. Verificar `CORS_ORIGINS` no Render inclui seu domínio
2. Verificar `REACT_APP_BACKEND_URL` no build do frontend

### MongoDB não conecta
1. Verificar `MONGO_URL` correto no Render
2. Verificar Network Access no MongoDB Atlas (0.0.0.0/0)
3. Testar conexão manualmente

---

## 📊 Comparativo: VPS vs Híbrido

| Aspecto | VPS | Híbrido (Hostinger + Render) |
|---------|-----|------------------------------|
| Custo | ~$5-10/mês | Grátis (com limitações) |
| Setup | Complexo | Simples |
| Manutenção | Manual | Automática |
| Performance | Melhor | Boa (com cold start) |
| Escalabilidade | Manual | Automática |
| SSL | Manual (Certbot) | Incluído |
| Backup | Manual | Automático |

---

## ✅ Checklist Final

- [ ] MongoDB Atlas criado e configurado
- [ ] Backend deployado no Render
- [ ] Variáveis de ambiente configuradas
- [ ] Backend respondendo (testar URL)
- [ ] Frontend build gerado
- [ ] Frontend uploadado para Hostinger
- [ ] .htaccess configurado
- [ ] Admin criado
- [ ] Sistema testado (login, transcrição)
- [ ] Uptime monitor configurado (opcional)

---

## 🎉 Pronto!

Seu AudioMedic está rodando em produção usando hospedagem compartilhada!

**Acesse:** https://seudominio.com

---

## 📞 Próximos Passos

1. **Configurar Domínio:** Apontar para Hostinger no painel de DNS
2. **SSL:** Ativar SSL gratuito no painel Hostinger
3. **Uptime Monitor:** Configurar para manter backend ativo
4. **Backup:** Configurar backup automático no MongoDB Atlas
5. **Monitoramento:** Adicionar Google Analytics (opcional)

---

**Dúvidas?** Este método é ideal para começar sem VPS! 🚀
