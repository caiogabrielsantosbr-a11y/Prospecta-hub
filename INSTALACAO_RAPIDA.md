# 🚀 Instalação Rápida - Prospecta HUB

Guia simplificado para rodar o projeto rapidamente.

## ✅ Checklist de Instalação

### 1. Instalar Python 3.11+
- [ ] Baixar: https://www.python.org/downloads/
- [ ] ⚠️ **MARCAR**: "Add Python to PATH" durante instalação
- [ ] Testar: `python --version` no terminal

### 2. Instalar Node.js 18+
- [ ] Baixar: https://nodejs.org/
- [ ] Testar: `node --version` e `npm --version`

### 3. Criar Conta Supabase
- [ ] Criar conta: https://supabase.com
- [ ] Criar novo projeto
- [ ] Copiar credenciais (Settings > API):
  - Project URL
  - anon public key
  - service_role key

## 📝 Configuração Rápida

### Passo 1: Baixar o Projeto
```bash
# Opção 1: Com Git
git clone https://github.com/caiogabrielsantosbr-a11y/Prospecta-hub.git
cd Prospecta-hub

# Opção 2: Baixar ZIP e extrair
```

### Passo 2: Backend
```bash
cd backend

# Criar ambiente virtual
python -m venv venv

# Ativar (Windows)
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Instalar navegador Playwright
playwright install chromium
```

**Criar arquivo `backend/.env`**:
```env
SUPABASE_URL=cole_aqui_sua_url
SUPABASE_KEY=cole_aqui_sua_anon_key
SUPABASE_SERVICE_KEY=cole_aqui_sua_service_key
JWT_SECRET=qualquer_texto_aleatorio_secreto_123
```

### Passo 3: Frontend
```bash
cd ../frontend

# Instalar dependências
npm install
```

**Criar arquivo `frontend/.env`**:
```env
VITE_SUPABASE_URL=cole_aqui_sua_url
VITE_SUPABASE_ANON_KEY=cole_aqui_sua_anon_key
VITE_API_URL=http://localhost:8000
```

### Passo 4: Criar Tabelas no Supabase

1. Abra seu projeto no Supabase
2. Vá em **SQL Editor**
3. Cole e execute este SQL:

```sql
-- Habilitar extensões
create extension if not exists "uuid-ossp";

-- Tabela de usuários
create table public.users (
  id uuid references auth.users primary key,
  email text unique not null,
  full_name text,
  avatar_url text,
  backend_url text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Tabela de leads do Google Maps
create table public.gmap_leads (
  id bigserial primary key,
  user_id uuid references auth.users not null,
  nome text not null,
  telefone text,
  website text,
  endereco text,
  email text,
  cidade text,
  url text,
  conjunto_de_locais text,
  task_id text,
  synced_to_sheets boolean default false,
  created_at timestamptz default now()
);

-- Tabela de webhooks do Google Sheets
create table public.gsheets_webhooks (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references auth.users not null,
  name text not null,
  webhook_url text not null,
  description text,
  daily_limit integer default 80,
  active boolean default true,
  created_at timestamptz default now()
);

-- Tabela de configurações
create table public.app_settings (
  id bigserial primary key,
  user_id uuid references auth.users not null,
  key text not null,
  value text,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique(user_id, key)
);

-- Tabela de tarefas
create table public.tasks (
  id text primary key,
  user_id uuid references auth.users,
  module text not null,
  status text default 'running',
  config jsonb default '{}',
  stats jsonb default '{}',
  progress real default 0.0,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Habilitar RLS
alter table public.users enable row level security;
alter table public.gmap_leads enable row level security;
alter table public.gsheets_webhooks enable row level security;
alter table public.app_settings enable row level security;
alter table public.tasks enable row level security;

-- Políticas RLS
create policy "Users can view own data" on public.users for select using (auth.uid() = id);
create policy "Users can update own data" on public.users for update using (auth.uid() = id);

create policy "Users can view own leads" on public.gmap_leads for select using (auth.uid() = user_id);
create policy "Users can insert own leads" on public.gmap_leads for insert with check (auth.uid() = user_id);

create policy "Users can view own webhooks" on public.gsheets_webhooks for all using (auth.uid() = user_id);
create policy "Users can view own settings" on public.app_settings for all using (auth.uid() = user_id);
create policy "Users can view own tasks" on public.tasks for all using (auth.uid() = user_id);
```

## ▶️ Executar

### Opção 1: Script Automático (Windows)
Na raiz do projeto:
```bash
start.bat
```

### Opção 2: Manual

**Terminal 1 - Backend**:
```bash
cd backend
venv\Scripts\activate
python main.py
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev
```

## 🌐 Acessar

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## ❌ Problemas Comuns

### "Python não encontrado"
→ Reinstale Python marcando "Add to PATH"

### "playwright install falhou"
```bash
python -m playwright install chromium
```

### "Porta 8000 em uso"
→ Mude no `backend/.env`: `BACKEND_PORT=8001`

### "npm install falhou"
```bash
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### "Erro de conexão Supabase"
→ Verifique se:
- Credenciais no `.env` estão corretas
- Tabelas foram criadas no SQL Editor
- Políticas RLS estão ativas

## 📦 O que foi instalado?

### Backend (Python)
- FastAPI - Framework web
- Uvicorn - Servidor ASGI
- Playwright - Automação de navegador
- Supabase - Cliente do banco de dados
- httpx - Cliente HTTP assíncrono
- python-socketio - WebSockets

### Frontend (React)
- React 19 - Framework UI
- Vite - Build tool
- React Router - Roteamento
- Supabase JS - Cliente Supabase
- Socket.io - WebSockets
- Tailwind CSS - Estilização
- Lucide React - Ícones

## 🎯 Próximos Passos

1. Criar conta no sistema (http://localhost:5173)
2. Configurar Google Sheets webhook
3. Testar extração do Google Maps
4. Configurar agendamento de emails

## 📞 Precisa de Ajuda?

- Leia o README.md completo
- Verifique a documentação da API: http://localhost:8000/docs
- Entre em contato: caiogabrielsantosbr@gmail.com
