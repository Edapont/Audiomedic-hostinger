# 🚀 Guia de Deploy - AudioMedic no Hostinger

## 📋 Requisitos do Hostinger

### Plano Recomendado
- **VPS Hostinger** (mínimo VPS 1)
- Python 3.11+
- Node.js 18+
- MongoDB (pode usar MongoDB Atlas gratuito)
- 2GB RAM mínimo
- 20GB espaço em disco

---

## 🛠️ Preparação Pré-Deploy

### 1. MongoDB Setup

**Opção A: MongoDB Atlas (Recomendado - Gratuito)**
1. Criar conta em https://www.mongodb.com/cloud/atlas
2. Criar cluster gratuito (M0)
3. Criar usuário de banco de dados
4. Adicionar IP 0.0.0.0/0 nas Network Access (permitir todos)
5. Obter connection string:
   ```
   mongodb+srv://usuario:senha@cluster.mongodb.net/audiomedic_db?retryWrites=true&w=majority
   ```

**Opção B: MongoDB no VPS**
```bash
# Instalar MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod
```

### 2. Obter Credenciais SMTP (Opcional)

**Gmail:**
1. Ativar verificação em 2 etapas
2. Gerar App Password: https://myaccount.google.com/apppasswords
3. Usar nos settings: smtp.gmail.com:587

**Hostinger Email:**
- Host: smtp.hostinger.com
- Porta: 587
- Usar credenciais do email criado no painel

---

## 📦 Instalação no Hostinger VPS

### Passo 1: Conectar via SSH
```bash
ssh root@seu-ip-hostinger
```

### Passo 2: Instalar Dependências do Sistema
```bash
# Atualizar sistema
apt update && apt upgrade -y

# Instalar essenciais
apt install -y git curl wget software-properties-common

# Instalar Python 3.11
add-apt-repository ppa:deadsnakes/ppa -y
apt update
apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Instalar Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Instalar Nginx
apt install -y nginx

# Instalar Supervisor
apt install -y supervisor

# Instalar build tools
apt install -y build-essential
```

### Passo 3: Clonar Projeto
```bash
# Criar diretório
mkdir -p /var/www/audiomedic
cd /var/www/audiomedic

# Se tiver GitHub, clonar:
# git clone https://github.com/seu-usuario/audiomedic.git .

# Ou fazer upload dos arquivos via SCP/FTP
```

### Passo 4: Configurar Backend
```bash
cd /var/www/audiomedic/backend

# Criar ambiente virtual
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# Criar arquivo .env
cat > .env << 'EOF'
# MongoDB
MONGO_URL=mongodb+srv://usuario:senha@cluster.mongodb.net/audiomedic_db
DB_NAME=audiomedic_db

# CORS
CORS_ORIGINS=https://seudominio.com,https://www.seudominio.com

# JWT
JWT_SECRET=GERAR_STRING_ALEATORIA_AQUI_64_CHARS_MIN
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# OpenAI (suas chaves)
EMERGENT_LLM_KEY=sua_chave_aqui
OPENAI_API_KEY=sua_chave_openai_aqui

# SMTP (opcional)
SMTP_HOST=smtp.hostinger.com
SMTP_PORT=587
SMTP_USER=noreply@seudominio.com
SMTP_PASSWORD=sua_senha_email
SMTP_FROM_EMAIL=noreply@seudominio.com
SMTP_FROM_NAME=AudioMedic
SMTP_USE_TLS=true

# Frontend URL
FRONTEND_URL=https://seudominio.com
EOF

# Gerar JWT_SECRET seguro
python3 -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(64))" >> .env.tmp

# Desativar venv
deactivate
```

### Passo 5: Configurar Frontend
```bash
cd /var/www/audiomedic/frontend

# Instalar yarn
npm install -g yarn

# Instalar dependências
yarn install

# Criar .env de produção
cat > .env.production << 'EOF'
REACT_APP_BACKEND_URL=https://seudominio.com
REACT_APP_ENABLE_VISUAL_EDITS=false
ENABLE_HEALTH_CHECK=false
EOF

# Build de produção
yarn build

# Resultado fica em /var/www/audiomedic/frontend/build
```

---

## ⚙️ Configuração do Servidor

### 1. Supervisor (Backend)
```bash
cat > /etc/supervisor/conf.d/audiomedic-backend.conf << 'EOF'
[program:audiomedic-backend]
directory=/var/www/audiomedic/backend
command=/var/www/audiomedic/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/audiomedic/backend.err.log
stdout_logfile=/var/log/audiomedic/backend.out.log
environment=PATH="/var/www/audiomedic/backend/venv/bin"
EOF

# Criar diretório de logs
mkdir -p /var/log/audiomedic
chown -R www-data:www-data /var/log/audiomedic

# Recarregar supervisor
supervisorctl reread
supervisorctl update
supervisorctl start audiomedic-backend
```

### 2. Nginx (Frontend + Backend Proxy)
```bash
# Remover configuração padrão
rm /etc/nginx/sites-enabled/default

# Criar configuração AudioMedic
cat > /etc/nginx/sites-available/audiomedic << 'EOF'
server {
    listen 80;
    server_name seudominio.com www.seudominio.com;
    
    # Redirecionar HTTP para HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name seudominio.com www.seudominio.com;
    
    # SSL Certificate (configurar depois com Certbot)
    ssl_certificate /etc/letsencrypt/live/seudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seudominio.com/privkey.pem;
    
    # SSL Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Frontend (React build)
    root /var/www/audiomedic/frontend/build;
    index index.html;
    
    # Frontend routes
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Backend API proxy
    location /api/ {
        proxy_pass http://localhost:8001/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Static files cache
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Logs
    access_log /var/log/nginx/audiomedic_access.log;
    error_log /var/log/nginx/audiomedic_error.log;
}
EOF

# Ativar site
ln -s /etc/nginx/sites-available/audiomedic /etc/nginx/sites-enabled/

# Testar configuração
nginx -t

# Reiniciar Nginx
systemctl restart nginx
```

### 3. SSL Certificate (Let's Encrypt)
```bash
# Instalar Certbot
apt install -y certbot python3-certbot-nginx

# Obter certificado (ajustar domínio)
certbot --nginx -d seudominio.com -d www.seudominio.com

# Renovação automática já está configurada
# Testar renovação:
certbot renew --dry-run
```

---

## 🔧 Configuração Pós-Deploy

### 1. Criar Usuário Admin
```bash
cd /var/www/audiomedic/backend
source venv/bin/activate

python3 << 'EOF'
from pymongo import MongoClient
import bcrypt
import uuid
from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]

# Dados do admin
admin_email = "admin@seudominio.com"
admin_password = "SenhaForte123!@#"  # MUDAR DEPOIS DO LOGIN
admin_name = "Administrador"

# Hash da senha
hashed_pw = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')

# Criar admin
admin_id = str(uuid.uuid4())
trial_end = datetime.now(timezone.utc) + timedelta(days=365)

admin_doc = {
    "id": admin_id,
    "email": admin_email,
    "name": admin_name,
    "hashed_password": hashed_pw,
    "subscription_status": "active",
    "subscription_end_date": trial_end.isoformat(),
    "is_admin": True,
    "email_verified": True,
    "created_at": datetime.now(timezone.utc).isoformat()
}

# Verificar se já existe
existing = db.users.find_one({"email": admin_email})
if existing:
    print(f"Admin já existe: {admin_email}")
else:
    db.users.insert_one(admin_doc)
    print(f"✅ Admin criado: {admin_email}")
    print(f"   Senha temporária: {admin_password}")
    print(f"   TROQUE A SENHA APÓS O PRIMEIRO LOGIN!")

client.close()
EOF

deactivate
```

### 2. Configurar Firewall
```bash
# Configurar UFW
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable
```

### 3. Verificar Serviços
```bash
# Verificar backend
supervisorctl status audiomedic-backend

# Ver logs
tail -f /var/log/audiomedic/backend.err.log

# Verificar Nginx
systemctl status nginx

# Ver logs Nginx
tail -f /var/log/nginx/audiomedic_error.log

# Testar API
curl -I http://localhost:8001/api/
```

---

## 🧪 Testes Pós-Deploy

### 1. Testar Backend
```bash
# Health check
curl https://seudominio.com/api/

# Testar registro
curl -X POST https://seudominio.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"teste@teste.com","password":"TesteForte123!","name":"Teste User"}'
```

### 2. Testar Frontend
1. Acessar https://seudominio.com
2. Fazer login com admin
3. Criar nova transcrição
4. Verificar painel admin

---

## 🔄 Updates e Manutenção

### Deploy de Updates
```bash
cd /var/www/audiomedic

# Pull latest changes (se usando git)
git pull

# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
deactivate
supervisorctl restart audiomedic-backend

# Frontend
cd ../frontend
yarn install
yarn build
systemctl reload nginx
```

### Backup Database
```bash
# Criar backup
mongodump --uri="MONGO_URL" --out=/backups/audiomedic-$(date +%Y%m%d)

# Restore
mongorestore --uri="MONGO_URL" /backups/audiomedic-YYYYMMDD
```

### Logs
```bash
# Backend logs
tail -f /var/log/audiomedic/backend.err.log

# Nginx logs
tail -f /var/log/nginx/audiomedic_error.log

# Supervisor logs
tail -f /var/log/supervisor/supervisord.log
```

---

## ⚠️ Troubleshooting

### Backend não inicia
```bash
# Verificar logs
tail -n 100 /var/log/audiomedic/backend.err.log

# Verificar permissões
chown -R www-data:www-data /var/www/audiomedic

# Testar manualmente
cd /var/www/audiomedic/backend
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001
```

### Frontend não carrega
```bash
# Verificar build
ls -la /var/www/audiomedic/frontend/build

# Rebuild
cd /var/www/audiomedic/frontend
yarn build

# Verificar Nginx
nginx -t
systemctl restart nginx
```

### Erro de conexão MongoDB
```bash
# Testar conexão
python3 << 'EOF'
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv('/var/www/audiomedic/backend/.env')
try:
    client = MongoClient(os.environ['MONGO_URL'])
    print(client.server_info())
    print("✅ MongoDB conectado!")
except Exception as e:
    print(f"❌ Erro: {e}")
EOF
```

---

## 📊 Monitoramento

### Setup Monitoring (Opcional)
```bash
# Instalar PM2 para monitoramento
npm install -g pm2

# Monitor backend com PM2
pm2 start /var/www/audiomedic/backend/venv/bin/uvicorn \
  --name audiomedic-backend \
  -- server:app --host 0.0.0.0 --port 8001

# Dashboard
pm2 monit
```

---

## ✅ Checklist Final

- [ ] MongoDB configurado e acessível
- [ ] Variáveis de ambiente configuradas (.env)
- [ ] Dependências instaladas (backend e frontend)
- [ ] Frontend build gerado
- [ ] Supervisor configurado e rodando
- [ ] Nginx configurado
- [ ] SSL/HTTPS ativo (Let's Encrypt)
- [ ] Firewall configurado (UFW)
- [ ] Admin criado no banco
- [ ] Testes básicos funcionando
- [ ] Backups configurados
- [ ] Logs acessíveis

---

## 🆘 Suporte

Em caso de problemas:
1. Verificar logs (backend, nginx, supervisor)
2. Testar conexões (MongoDB, API endpoints)
3. Validar variáveis de ambiente
4. Checar permissões de arquivos

---

**Deploy preparado para produção! 🚀**
