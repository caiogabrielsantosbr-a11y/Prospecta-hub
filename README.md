# Prospecta HUB

Plataforma unificada de prospecção com integração Google Maps, Facebook ADS, Email e Google Sheets.

## 📋 Pré-requisitos

Antes de começar, você precisa ter instalado:

### 1. Python 3.11 ou superior
- **Windows**: Baixe em [python.org](https://www.python.org/downloads/)
  - ⚠️ **IMPORTANTE**: Marque a opção "Add Python to PATH" durante a instalação
- **Verificar instalação**:
  ```bash
  python --version
  ```

### 2. Node.js 18 ou superior
- **Windows**: Baixe em [nodejs.org](https://nodejs.org/)
- **Verificar instalação**:
  ```bash
  node --version
  npm --version
  ```

### 3. Git (opcional, mas recomendado)
- **Windows**: Baixe em [git-scm.com](https://git-scm.com/)

## 🚀 Instalação

### Passo 1: Clonar o Repositório

```bash
git clone https://github.com/caiogabrielsantosbr-a11y/Prospecta-hub.git
cd Prospecta-hub
```

Ou baixe o ZIP e extraia.

### Passo 2: Configurar Backend (Python)

1. **Criar ambiente virtual** (recomendado):
   ```bash
   cd backend
   python -m venv venv
   ```

2. **Ativar ambiente virtual**:
   - **Windows**:
     ```bash
     venv\Scripts\activate
     ```
   - **Linux/Mac**:
     ```bash
     source venv/bin/activate
     ```

3. **Instalar dependências**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Instalar Playwright browsers** (necessário para Google Maps):
   ```bash
   playwright install chromium
   ```

5. **Criar arquivo `.env`** na pasta `backend`:
   ```env
   # Supabase (obrigatório)
   SUPABASE_URL=sua_url_do_supabase
   SUPABASE_KEY=sua_chave_anon_do_supabase
   SUPABASE_SERVICE_KEY=sua_service_role_key_do_supabase

   # JWT Secret (obrigatório)
   JWT_SECRET=sua_chave_secreta_aleatoria_aqui

   # Opcional: Configurações adicionais
   BACKEND_PORT=8000
   ```

### Passo 3: Configurar Frontend (React)

1. **Ir para pasta frontend**:
   ```bash
   cd ../frontend
   ```

2. **Instalar dependências**:
   ```bash
   npm install
   ```

3. **Criar arquivo `.env`** na pasta `frontend`:
   ```env
   VITE_SUPABASE_URL=sua_url_do_supabase
   VITE_SUPABASE_ANON_KEY=sua_chave_anon_do_supabase
   VITE_API_URL=http://localhost:8000
   ```

### Passo 4: Configurar Supabase

1. **Criar conta no Supabase**: [supabase.com](https://supabase.com)

2. **Criar novo projeto**

3. **Executar SQL para criar tabelas** (vá em SQL Editor no Supabase):

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

-- Tabela de configurações do app
create table public.app_settings (
  id bigserial primary key,
  user_id uuid references auth.users not null,
  key text not null,
  value text,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique(user_id, key)
);

-- Habilitar RLS (Row Level Security)
alter table public.users enable row level security;
alter table public.gmap_leads enable row level security;
alter table public.gsheets_webhooks enable row level security;
alter table public.app_settings enable row level security;

-- Políticas RLS
create policy "Users can view own data" on public.users for select using (auth.uid() = id);
create policy "Users can update own data" on public.users for update using (auth.uid() = id);

create policy "Users can view own leads" on public.gmap_leads for select using (auth.uid() = user_id);
create policy "Users can insert own leads" on public.gmap_leads for insert with check (auth.uid() = user_id);

create policy "Users can view own webhooks" on public.gsheets_webhooks for all using (auth.uid() = user_id);

create policy "Users can view own settings" on public.app_settings for all using (auth.uid() = user_id);
```

4. **Copiar credenciais**:
   - Vá em **Settings > API**
   - Copie `Project URL` → `SUPABASE_URL`
   - Copie `anon public` → `SUPABASE_KEY` / `VITE_SUPABASE_ANON_KEY`
   - Copie `service_role` → `SUPABASE_SERVICE_KEY` (⚠️ mantenha secreto!)

## ▶️ Executar o Projeto

### Opção 1: Usar o script start.bat (Windows)

Na raiz do projeto, execute:
```bash
start.bat
```

Isso irá:
1. Iniciar o backend na porta 8000
2. Iniciar o frontend na porta 5173

### Opção 2: Executar manualmente

**Terminal 1 - Backend**:
```bash
cd backend
venv\Scripts\activate  # Windows
# ou: source venv/bin/activate  # Linux/Mac
python main.py
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev
```

## 🌐 Acessar a Aplicação

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **Documentação API**: http://localhost:8000/docs

## 📦 Estrutura do Projeto

```
Prospecta-hub/
├── backend/              # API Python (FastAPI)
│   ├── database/         # Integração Supabase
│   ├── modules/          # Módulos (gmap, facebook, email)
│   ├── requirements.txt  # Dependências Python
│   └── main.py          # Entry point
├── frontend/            # Interface React
│   ├── src/
│   │   ├── components/  # Componentes React
│   │   ├── pages/       # Páginas
│   │   ├── services/    # API client
│   │   └── contexts/    # Context providers
│   ├── package.json     # Dependências Node
│   └── vite.config.js   # Configuração Vite
├── Extensao appscript/  # Google Apps Script
│   ├── Code.gs          # Lógica principal
│   └── Sidebar.html     # Interface
└── start.bat            # Script de inicialização
```

## 🔧 Configuração da Extensão Google Sheets

1. Abra uma planilha no Google Sheets
2. Vá em **Extensões > Apps Script**
3. Cole o conteúdo de `Extensao appscript/Code.gs`
4. Crie um arquivo HTML chamado `Sidebar` e cole o conteúdo de `Sidebar.html`
5. Salve e faça deploy como **Web App**
6. Copie a URL do deployment e adicione no Prospecta HUB

## 🐛 Solução de Problemas

### Erro: "Python não encontrado"
- Reinstale o Python marcando "Add to PATH"
- Ou adicione manualmente ao PATH do sistema

### Erro: "playwright install falhou"
```bash
# Tente instalar manualmente
python -m playwright install chromium
```

### Erro: "Porta 8000 já em uso"
- Mude a porta no `.env`: `BACKEND_PORT=8001`
- Ou mate o processo: `taskkill /F /IM python.exe` (Windows)

### Erro: "npm install falhou"
- Limpe o cache: `npm cache clean --force`
- Delete `node_modules` e `package-lock.json`
- Execute `npm install` novamente

### Erro de conexão com Supabase
- Verifique se as credenciais no `.env` estão corretas
- Verifique se as tabelas foram criadas no Supabase
- Verifique se as políticas RLS estão ativas

## 📝 Variáveis de Ambiente

### Backend (.env)
```env
SUPABASE_URL=              # URL do projeto Supabase
SUPABASE_KEY=              # Chave anon pública
SUPABASE_SERVICE_KEY=      # Service role key (privada)
JWT_SECRET=                # Chave secreta para JWT
BACKEND_PORT=8000          # Porta do backend (opcional)
```

### Frontend (.env)
```env
VITE_SUPABASE_URL=         # URL do projeto Supabase
VITE_SUPABASE_ANON_KEY=    # Chave anon pública
VITE_API_URL=http://localhost:8000  # URL do backend
```

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch: `git checkout -b feature/nova-feature`
3. Commit suas mudanças: `git commit -m 'Add nova feature'`
4. Push para a branch: `git push origin feature/nova-feature`
5. Abra um Pull Request

## 📄 Licença

Este projeto é privado e proprietário.

## 👥 Autores

- **Caio Gabriel Santos** - [GitHub](https://github.com/caiogabrielsantosbr-a11y)

## 🆘 Suporte

Para dúvidas ou problemas:
- Abra uma issue no GitHub
- Entre em contato: caiogabrielsantosbr@gmail.com
