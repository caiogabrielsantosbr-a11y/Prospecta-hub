# 🏗️ Arquitetura do Sistema de Usuários

## 📐 Visão Geral

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  LoginPage   │  │ ProfilePage  │  │  LeadsPage   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                  │                   │
│         └─────────────────┼──────────────────┘                   │
│                           │                                      │
│                  ┌────────▼────────┐                            │
│                  │  AuthContext    │                            │
│                  │  - user         │                            │
│                  │  - profile      │                            │
│                  │  - signIn()     │                            │
│                  │  - signOut()    │                            │
│                  └────────┬────────┘                            │
│                           │                                      │
└───────────────────────────┼──────────────────────────────────────┘
                            │
                            │ JWT Token
                            │
┌───────────────────────────▼──────────────────────────────────────┐
│                      BACKEND (FastAPI)                            │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Middleware                             │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  auth.py                                           │  │   │
│  │  │  - get_current_user()  → Valida JWT                │  │   │
│  │  │  - get_optional_user() → Opcional                  │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                              │                                   │
│  ┌───────────────────────────▼───────────────────────────────┐  │
│  │                       Routers                              │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │ leads/       │  │ gmap/        │  │ facebook/    │   │  │
│  │  │ router.py    │  │ router.py    │  │ router.py    │   │  │
│  │  │              │  │              │  │              │   │  │
│  │  │ + user_id    │  │ + user_id    │  │ + user_id    │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │
                               │ SQL + RLS
                               │
┌──────────────────────────────▼───────────────────────────────────┐
│                    SUPABASE (PostgreSQL)                          │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    Auth (Supabase Auth)                     │  │
│  │  - Gerencia usuários                                        │  │
│  │  - Gera JWT tokens                                          │  │
│  │  - Valida credenciais                                       │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    Database (PostgreSQL)                    │  │
│  │                                                             │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  users (perfil estendido)                            │  │  │
│  │  │  - id → auth.users                                   │  │  │
│  │  │  - email, full_name, avatar_url, backend_url        │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │                                                             │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  Tabelas com user_id (ISOLADAS)                      │  │  │
│  │  │  - gmap_leads                                        │  │  │
│  │  │  - facebook_ads_leads                                │  │  │
│  │  │  - email_results                                     │  │  │
│  │  │  - tasks                                             │  │  │
│  │  │  - email_dispatches                                  │  │  │
│  │  │                                                       │  │  │
│  │  │  RLS: WHERE user_id = auth.uid()                     │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │                                                             │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  Tabelas compartilhadas (SEM user_id)                │  │  │
│  │  │  - location_sets                                     │  │  │
│  │  │  - app_settings                                      │  │  │
│  │  │                                                       │  │  │
│  │  │  RLS: WHERE auth.role() = 'authenticated'            │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    Storage (Supabase Storage)               │  │
│  │  - Bucket: avatars (público)                                │  │
│  │  - RLS: Usuários podem fazer upload de suas fotos          │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

## 🔄 Fluxo de Autenticação

```
1. CADASTRO
   ┌─────────┐
   │ Usuário │
   └────┬────┘
        │ 1. Preenche formulário
        ▼
   ┌─────────────┐
   │ LoginPage   │
   └────┬────────┘
        │ 2. signUp(email, password, name)
        ▼
   ┌─────────────┐
   │ AuthContext │
   └────┬────────┘
        │ 3. supabase.auth.signUp()
        ▼
   ┌──────────────┐
   │ Supabase     │
   │ Auth         │
   └────┬─────────┘
        │ 4. Cria usuário em auth.users
        │ 5. Trigger cria perfil em users
        ▼
   ┌──────────────┐
   │ users table  │
   └──────────────┘

2. LOGIN
   ┌─────────┐
   │ Usuário │
   └────┬────┘
        │ 1. Preenche email/senha
        ▼
   ┌─────────────┐
   │ LoginPage   │
   └────┬────────┘
        │ 2. signIn(email, password)
        ▼
   ┌─────────────┐
   │ AuthContext │
   └────┬────────┘
        │ 3. supabase.auth.signInWithPassword()
        ▼
   ┌──────────────┐
   │ Supabase     │
   │ Auth         │
   └────┬─────────┘
        │ 4. Valida credenciais
        │ 5. Retorna JWT token
        ▼
   ┌──────────────┐
   │ AuthContext  │
   │ (armazena    │
   │  token)      │
   └──────────────┘

3. REQUISIÇÃO AUTENTICADA
   ┌─────────┐
   │ Usuário │
   └────┬────┘
        │ 1. Acessa /leads
        ▼
   ┌─────────────┐
   │ LeadsPage   │
   └────┬────────┘
        │ 2. fetch('/api/leads', {
        │      headers: { Authorization: 'Bearer TOKEN' }
        │    })
        ▼
   ┌──────────────┐
   │ Backend      │
   │ Middleware   │
   └────┬─────────┘
        │ 3. Valida JWT token
        │ 4. Extrai user_id
        ▼
   ┌──────────────┐
   │ Router       │
   │ (leads)      │
   └────┬─────────┘
        │ 5. SELECT * FROM gmap_leads
        │    WHERE user_id = ?
        ▼
   ┌──────────────┐
   │ Supabase DB  │
   │ (RLS ativo)  │
   └────┬─────────┘
        │ 6. Filtra por user_id
        │ 7. Retorna apenas dados do usuário
        ▼
   ┌──────────────┐
   │ LeadsPage    │
   │ (exibe dados)│
   └──────────────┘
```

## 🔐 Camadas de Segurança

```
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA 1: FRONTEND                        │
│  - Rotas protegidas (ProtectedRoute)                        │
│  - Redirecionamento automático para /login                  │
│  - Token armazenado em localStorage                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA 2: BACKEND                         │
│  - Middleware valida JWT em cada requisição                 │
│  - Extrai user_id do token                                  │
│  - Rejeita requisições sem token ou com token inválido      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA 3: BANCO DE DADOS                  │
│  - Row Level Security (RLS) ativo                           │
│  - Políticas filtram por auth.uid()                         │
│  - Impossível acessar dados de outros usuários              │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Isolamento de Dados

```
┌──────────────────────────────────────────────────────────────┐
│                         USUÁRIO A                             │
├──────────────────────────────────────────────────────────────┤
│  user_id: 123e4567-e89b-12d3-a456-426614174000              │
│                                                               │
│  Pode ver/editar:                                            │
│  ✅ gmap_leads WHERE user_id = 123e4567...                   │
│  ✅ tasks WHERE user_id = 123e4567...                        │
│  ✅ email_dispatches WHERE user_id = 123e4567...             │
│  ✅ location_sets (todos)                                    │
│                                                               │
│  NÃO pode ver:                                               │
│  ❌ gmap_leads WHERE user_id = 987f6543...                   │
│  ❌ tasks WHERE user_id = 987f6543...                        │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                         USUÁRIO B                             │
├──────────────────────────────────────────────────────────────┤
│  user_id: 987f6543-e89b-12d3-a456-426614174111              │
│                                                               │
│  Pode ver/editar:                                            │
│  ✅ gmap_leads WHERE user_id = 987f6543...                   │
│  ✅ tasks WHERE user_id = 987f6543...                        │
│  ✅ email_dispatches WHERE user_id = 987f6543...             │
│  ✅ location_sets (todos)                                    │
│                                                               │
│  NÃO pode ver:                                               │
│  ❌ gmap_leads WHERE user_id = 123e4567...                   │
│  ❌ tasks WHERE user_id = 123e4567...                        │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    DADOS COMPARTILHADOS                       │
├──────────────────────────────────────────────────────────────┤
│  location_sets (sem user_id)                                 │
│  - Todos os usuários autenticados podem ver/editar           │
│  - Usado para compartilhar conjuntos de locais               │
│                                                               │
│  app_settings (sem user_id)                                  │
│  - Todos os usuários autenticados podem ver                  │
│  - Configurações globais da aplicação                        │
└──────────────────────────────────────────────────────────────┘
```

## 🗂️ Estrutura de Tabelas

```
┌─────────────────────────────────────────────────────────────┐
│                         auth.users                           │
│  (Gerenciado pelo Supabase Auth)                            │
├─────────────────────────────────────────────────────────────┤
│  id (UUID)                                                   │
│  email                                                       │
│  encrypted_password                                          │
│  created_at                                                  │
│  ...                                                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ FK
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                         users                                │
│  (Perfil estendido)                                         │
├─────────────────────────────────────────────────────────────┤
│  id (UUID) → auth.users.id                                  │
│  email                                                       │
│  full_name                                                   │
│  avatar_url                                                  │
│  backend_url                                                 │
│  created_at                                                  │
│  updated_at                                                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ FK (user_id)
                         │
         ┌───────────────┼───────────────┬──────────────┐
         │               │               │              │
         ▼               ▼               ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────────┐
│ gmap_leads   │ │ facebook_ads │ │  tasks   │ │email_dispatch│
│              │ │    _leads    │ │          │ │              │
├──────────────┤ ├──────────────┤ ├──────────┤ ├──────────────┤
│ id           │ │ id           │ │ id       │ │ id           │
│ nome         │ │ name         │ │ module   │ │ recipient    │
│ telefone     │ │ page_url     │ │ status   │ │ subject      │
│ ...          │ │ ...          │ │ ...      │ │ ...          │
│ user_id ✅   │ │ user_id ✅   │ │user_id✅ │ │ user_id ✅   │
└──────────────┘ └──────────────┘ └──────────┘ └──────────────┘

┌─────────────────────────────────────────────────────────────┐
│              Tabelas Compartilhadas (sem user_id)            │
├─────────────────────────────────────────────────────────────┤
│  location_sets                                               │
│  - Conjuntos de locais compartilhados                       │
│                                                              │
│  app_settings                                                │
│  - Configurações globais                                     │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Ciclo de Vida de uma Requisição

```
1. Usuário faz requisição
   │
   ▼
2. Frontend adiciona token JWT no header
   │
   ▼
3. Backend recebe requisição
   │
   ▼
4. Middleware valida token
   │
   ├─ Token inválido → 401 Unauthorized
   │
   └─ Token válido
      │
      ▼
5. Middleware extrai user_id do token
   │
   ▼
6. Router recebe user_id como parâmetro
   │
   ▼
7. Query ao banco inclui WHERE user_id = ?
   │
   ▼
8. RLS do Supabase valida novamente
   │
   ├─ user_id não corresponde → Retorna vazio
   │
   └─ user_id corresponde
      │
      ▼
9. Dados retornados ao frontend
   │
   ▼
10. Frontend exibe dados
```

## 📦 Componentes do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                      AUTENTICAÇÃO                            │
├─────────────────────────────────────────────────────────────┤
│  Frontend:                                                   │
│  - AuthContext.jsx (gerencia estado)                        │
│  - LoginPage.jsx (UI de login/cadastro)                     │
│                                                              │
│  Backend:                                                    │
│  - middleware/auth.py (valida JWT)                          │
│                                                              │
│  Banco:                                                      │
│  - auth.users (Supabase Auth)                               │
│  - users (perfil estendido)                                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                         PERFIL                               │
├─────────────────────────────────────────────────────────────┤
│  Frontend:                                                   │
│  - ProfilePage.jsx (UI de perfil)                           │
│  - TopBar.jsx (menu de perfil)                              │
│                                                              │
│  Backend:                                                    │
│  - Usa Supabase diretamente (sem endpoint custom)           │
│                                                              │
│  Banco:                                                      │
│  - users (dados do perfil)                                  │
│  - storage.avatars (fotos)                                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      DADOS ISOLADOS                          │
├─────────────────────────────────────────────────────────────┤
│  Frontend:                                                   │
│  - LeadsPage.jsx, GMapPage.jsx, etc.                        │
│                                                              │
│  Backend:                                                    │
│  - modules/leads/router.py (exemplo)                        │
│  - modules/gmap/router.py (a atualizar)                     │
│  - modules/facebook/router.py (a atualizar)                 │
│                                                              │
│  Banco:                                                      │
│  - gmap_leads (com user_id)                                 │
│  - facebook_ads_leads (com user_id)                         │
│  - tasks (com user_id)                                      │
│  - email_dispatches (com user_id)                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   DADOS COMPARTILHADOS                       │
├─────────────────────────────────────────────────────────────┤
│  Frontend:                                                   │
│  - LocationSetsPage.jsx (se existir)                        │
│                                                              │
│  Backend:                                                    │
│  - Endpoints sem filtro de user_id                          │
│                                                              │
│  Banco:                                                      │
│  - location_sets (sem user_id)                              │
│  - app_settings (sem user_id)                               │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 Pontos-Chave da Arquitetura

1. **Autenticação Centralizada**: Supabase Auth gerencia tudo
2. **Validação em Múltiplas Camadas**: Frontend, Backend e Banco
3. **Isolamento Automático**: RLS garante segurança no banco
4. **Compartilhamento Seletivo**: Location_sets acessíveis a todos
5. **Perfil Estendido**: Dados adicionais além do Supabase Auth
6. **Storage Seguro**: Fotos isoladas por usuário

---

📖 **Documentação Completa**: `USER_SYSTEM_README.md`
