# 🏗️ Arquiteturas de Deploy - AudioMedic

## 📊 Comparação Visual

### Arquitetura 1: Hospedagem Compartilhada (Anterior)
```
┌─────────────────────────────────────────────────────────────┐
│                         Internet                             │
└──────────────┬──────────────────────────┬───────────────────┘
               │                          │
               │                          │
   ┌───────────▼──────────┐   ┌──────────▼──────────┐
   │  Hostinger Shared    │   │    Render.com       │
   │   (Frontend only)    │   │   (Backend only)    │
   │                      │   │                     │
   │  - React (static)    │   │  - FastAPI Python   │
   │  - .htaccess         │   │  - uvicorn          │
   │  - public_html/      │   │  - Auto-deploy      │
   │                      │   │  - Dorme após 15min │
   └──────────────────────┘   └──────────┬──────────┘
                                         │
                              ┌──────────▼──────────┐
                              │   MongoDB Atlas     │
                              │   (Cloud Database)  │
                              │                     │
                              │  - M0 Free Tier     │
                              │  - 512MB storage    │
                              └─────────────────────┘
```

**Limitações:**
- ❌ Backend "dorme" após inatividade (cold start ~30s)
- ❌ Dois serviços separados (complexidade)
- ❌ Render Free Tier tem limitações
- ⚠️ Requer configuração CORS entre domínios
- ⚠️ Deploy em dois lugares diferentes

---

### Arquitetura 2: VPS Privado (Atual - Recomendado) ✅
```
┌─────────────────────────────────────────────────────────────┐
│                         Internet                             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ HTTPS (443)
                           │
               ┌───────────▼──────────────┐
               │   Hostinger VPS          │
               │   (seu-dominio.com)      │
               │                          │
               │  ┌──────────────────┐    │
               │  │     Nginx        │    │
               │  │  (Proxy Reverso) │    │
               │  └───┬──────────┬───┘    │
               │      │          │        │
               │  ┌───▼────┐ ┌──▼─────┐  │
               │  │Frontend│ │Backend │  │
               │  │        │ │        │  │
               │  │ React  │ │FastAPI │  │
               │  │ Static │ │:8001   │  │
               │  │ Files  │ │        │  │
               │  └────────┘ └────────┘  │
               │                          │
               │  ┌──────────────────┐    │
               │  │   Supervisor     │    │
               │  │ (Gerencia procs) │    │
               │  └──────────────────┘    │
               └──────────┬───────────────┘
                          │
               ┌──────────▼───────────┐
               │   MongoDB Atlas      │
               │ (ou MongoDB Local)   │
               │                      │
               │  - Sempre disponível │
               │  - Backup automático │
               └──────────────────────┘
```

**Vantagens:**
- ✅ Backend sempre ativo (sem cold start)
- ✅ Tudo em um único servidor (simplicidade)
- ✅ Controle total (SSH, logs, processos)
- ✅ Melhor performance (mesma máquina)
- ✅ Deploy unificado
- ✅ CORS simplificado (mesmo domínio)
- ✅ MongoDB pode ser local (opcional)

---

## 🔧 Componentes do VPS

### Nginx
**Papel:** Servidor web e proxy reverso
- Serve arquivos estáticos do React (frontend)
- Faz proxy das requisições `/api/*` para o backend (porta 8001)
- Gerencia SSL/HTTPS (certificados Let's Encrypt)
- Compressão gzip
- Cache de assets estáticos

**Configuração:** `/etc/nginx/sites-available/audiomedic`

---

### Supervisor
**Papel:** Gerenciador de processos
- Mantém o backend FastAPI rodando
- Reinicia automaticamente se cair
- Logs centralizados
- Controle de processos (`supervisorctl status`)

**Configuração:** `/etc/supervisor/conf.d/audiomedic.conf`

---

### Backend (FastAPI)
**Papel:** API REST
- Roda na porta 8001 (interno)
- Gerenciado pelo Supervisor
- Python 3.11 + venv
- Logs em `/var/log/audiomedic/`

**Localização:** `/var/www/audiomedic/backend/`

---

### Frontend (React)
**Papel:** Interface do usuário
- Build estático servido pelo Nginx
- Todos os assets otimizados
- Roteamento via React Router
- API calls para `https://seudominio.com/api/*`

**Localização:** `/var/www/audiomedic/frontend/build/`

---

### MongoDB
**Opção A: MongoDB Atlas (Recomendado)**
- ✅ Backup automático
- ✅ Redundância
- ✅ 512MB grátis
- ✅ Fácil de escalar

**Opção B: MongoDB Local no VPS**
- ✅ Mais rápido (latência zero)
- ✅ Mais privacidade
- ⚠️ Você gerencia backups
- ⚠️ Usa recursos do VPS

---

## 📁 Estrutura de Arquivos no VPS

```
/var/www/audiomedic/
├── backend/
│   ├── .env                 # Variáveis de ambiente (MONGO_URL, JWT_SECRET, etc)
│   ├── venv/                # Python virtual environment
│   ├── server.py            # FastAPI app
│   ├── requirements.txt     # Dependências Python
│   └── create_admin.py      # Script criar admin
│
├── frontend/
│   ├── build/               # React build de produção
│   │   ├── index.html
│   │   ├── static/
│   │   │   ├── css/
│   │   │   └── js/
│   │   └── manifest.json
│   ├── src/                 # Código fonte React
│   └── package.json
│
├── DEPLOY_HOSTINGER.md      # Guia completo VPS
├── deploy_hostinger.sh      # Script de deploy automático
└── verify_deploy.sh         # Script de verificação

/etc/nginx/sites-available/audiomedic    # Config Nginx
/etc/supervisor/conf.d/audiomedic.conf   # Config Supervisor
/var/log/audiomedic/                     # Logs da aplicação
```

---

## 🔄 Fluxo de Requisição no VPS

### Requisição de Página (Frontend)
```
Usuário digita: https://seudominio.com
         ↓
    Nginx (443)
         ↓
Verifica se é arquivo estático
         ↓
Serve: /var/www/audiomedic/frontend/build/index.html
```

### Requisição de API (Backend)
```
Frontend faz: fetch('https://seudominio.com/api/auth/login')
         ↓
    Nginx (443)
         ↓
Detecta prefixo /api
         ↓
Proxy para: localhost:8001
         ↓
   Backend FastAPI
         ↓
Processa e retorna JSON
```

---

## 🚀 Comandos Essenciais VPS

### Gerenciar Backend
```bash
# Status
supervisorctl status audiomedic-backend

# Reiniciar
supervisorctl restart audiomedic-backend

# Logs em tempo real
tail -f /var/log/audiomedic/backend.err.log
```

### Gerenciar Frontend
```bash
# Rebuild
cd /var/www/audiomedic/frontend
yarn build

# Reiniciar Nginx
systemctl restart nginx
```

### Ver Logs
```bash
# Backend
tail -f /var/log/audiomedic/backend.err.log

# Nginx
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log

# Supervisor
tail -f /var/log/supervisor/supervisord.log
```

---

## ✅ Checklist de Migração

- [ ] **VPS Preparado**
  - [ ] SSH funcionando
  - [ ] Domínio apontando para VPS
  - [ ] Portas 80 e 443 abertas

- [ ] **Código Uploadado**
  - [ ] Projeto em `/var/www/audiomedic/`
  - [ ] Permissões corretas

- [ ] **Dependências Instaladas**
  - [ ] Python 3.11
  - [ ] Node.js 18
  - [ ] Nginx
  - [ ] Supervisor

- [ ] **Configuração**
  - [ ] backend/.env configurado
  - [ ] frontend/.env.production configurado
  - [ ] Nginx configurado
  - [ ] Supervisor configurado

- [ ] **SSL**
  - [ ] Certbot instalado
  - [ ] Certificados obtidos
  - [ ] HTTPS funcionando

- [ ] **Testes**
  - [ ] Backend: `curl https://seudominio.com/api/`
  - [ ] Frontend: navegador em `https://seudominio.com`
  - [ ] Login funciona
  - [ ] Admin criado

---

## 📞 Pronto para Deploy?

Execute:
```bash
./start_vps_deploy.sh
```

Este script vai te guiar por todo o processo! 🚀
