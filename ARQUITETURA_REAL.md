# 🏗️ Arquitetura Real do Sistema

## 📐 Visão Geral Correta

```
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND (React + Vite)                     │
│                                                                   │
│  - Interface do usuário                                          │
│  - Autenticação (Supabase Auth)                                 │
│  - Gerenciamento de estado (Zustand)                            │
│  - Comunicação direta com Supabase                              │
│  - WebSocket com backend local (apenas para tasks)              │
└───────────────┬─────────────────────────────┬───────────────────┘
                │                             │
                │ Supabase SDK                │ HTTP/WebSocket
                │ (dados, auth, storage)      │ (automações)
                │                             │
    ┌───────────▼──────────┐     ┌───────────▼──────────┐
    │                      │     │                       │
    │   SUPABASE           │     │  BACKEND LOCAL        │
    │   (Backend Real)     │     │  (Automações)         │
    │                      │     │                       │
    └──────────────────────┘     └───────────────────────┘
```

## 🎯 Responsabilidades

### SUPABASE (Backend Principal)
```
✅ Banco de Dados PostgreSQL
✅ Autenticação (Supabase Auth)
✅ Storage (fotos de perfil)
✅ Row Level Security (RLS)
✅ APIs REST automáticas
✅ Realtime subscriptions
✅ Edge Functions (se necessário)
```

### BACKEND LOCAL (FastAPI)
```
✅ Automações de scraping
   - Google Maps scraper
   - Facebook Ads scraper
   - Email extractor
✅ Workers assíncronos
✅ Task management
✅ WebSocket para status de tasks
✅ Integração com Playwright/Selenium
```

### FRONTEND (React)
```
✅ Interface do usuário
✅ Comunicação DIRETA com Supabase
   - CRUD de leads
   - Autenticação
   - Upload de fotos
   - Queries em tempo real
✅ Comunicação com backend local
   - Iniciar/parar automações
   - Receber status via WebSocket
```

## 🔄 Fluxos de Dados

### 1. AUTENTICAÇÃO (100% Supabase)
```
┌─────────┐
│ Usuário │
└────┬────┘
     │ 1. Login/Cadastro
     ▼
┌──────────────┐
│  Frontend    │
└────┬─────────┘
     │ 2. supabase.auth.signIn()
     ▼
┌──────────────┐
│  Supabase    │
│  Auth        │
└────┬─────────┘
     │ 3. Retorna JWT token
     ▼
┌──────────────┐
│  Frontend    │
│  (armazena   │
│   token)     │
└──────────────┘
```

### 2. CRUD DE LEADS (100% Supabase)
```
┌─────────┐
│ Usuário │
└────┬────┘
     │ 1. Ver/Editar/Deletar leads
     ▼
┌──────────────┐
│  Frontend    │
└────┬─────────┘
     │ 2. supabase.from('gmap_leads').select()
     ▼
┌──────────────┐
│  Supabase    │
│  Database    │
│  (RLS ativo) │
└────┬─────────┘
     │ 3. Retorna apenas dados do user_id
     ▼
┌──────────────┐
│  Frontend    │
│  (exibe)     │
└──────────────┘
```

### 3. AUTOMAÇÕES (Backend Local + Supabase)
```
┌─────────┐
│ Usuário │
└────┬────┘
     │ 1. Iniciar extração Google Maps
     ▼
┌──────────────┐
│  Frontend    │
└────┬─────────┘
     │ 2. POST /api/gmap/start
     ▼
┌──────────────┐
│  Backend     │
│  Local       │
│  (FastAPI)   │
└────┬─────────┘
     │ 3. Inicia worker (Playwright)
     │ 4. Extrai dados
     │ 5. Para cada lead encontrado:
     ▼
┌──────────────┐
│  Supabase    │
│  Database    │
└────┬─────────┘
     │ 6. INSERT com user_id
     │ 7. RLS valida
     ▼
┌──────────────┐
│  Frontend    │
│  (atualiza   │
│   via WS)    │
└──────────────┘
```

### 4. UPLOAD DE FOTO (100% Supabase)
```
┌─────────┐
│ Usuário │
└────┬────┘
     │ 1. Seleciona foto
     ▼
┌──────────────┐
│  Frontend    │
└────┬─────────┘
     │ 2. supabase.storage.upload()
     ▼
┌──────────────┐
│  Supabase    │
│  Storage     │
└────┬─────────┘
     │ 3. Retorna URL pública
     ▼
┌──────────────┐
│  Frontend    │
└────┬─────────┘
     │ 4. supabase.from('users').update()
     ▼
┌──────────────┐
│  Supabase    │
│  Database    │
└──────────────┘
```

## 🔐 Autenticação e Segurança

### Frontend → Supabase (DIRETO)
```javascript
// Autenticação
const { data, error } = await supabase.auth.signIn({
  email: 'user@email.com',
  password: 'senha'
})

// CRUD de leads (RLS automático)
const { data: leads } = await supabase
  .from('gmap_leads')
  .select('*')
  // RLS filtra automaticamente por user_id
```

### Frontend → Backend Local (COM TOKEN)
```javascript
// Obter token do Supabase
const { data: { session } } = await supabase.auth.getSession()
const token = session?.access_token

// Enviar para backend local
fetch(`${backendUrl}/api/gmap/start`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ config })
})
```

### Backend Local → Supabase (COM SERVICE KEY)
```python
# Backend usa service_role key para inserir dados
# (bypass RLS, mas inclui user_id manualmente)

supabase.table('gmap_leads').insert({
    'nome': business_name,
    'telefone': phone,
    'user_id': user_id,  # Do token JWT
    # ...
}).execute()
```

## 📊 Fluxo Completo de Extração

```
1. Usuário clica "Iniciar Extração"
   │
   ▼
2. Frontend envia para backend local
   POST /api/gmap/start
   Headers: { Authorization: Bearer <token> }
   Body: { locations, keywords, user_id }
   │
   ▼
3. Backend Local valida token JWT
   - Extrai user_id do token
   - Valida com SUPABASE_JWT_SECRET
   │
   ▼
4. Backend Local inicia worker
   - Playwright abre navegador
   - Navega no Google Maps
   - Extrai dados dos negócios
   │
   ▼
5. Para cada lead encontrado:
   Backend Local → Supabase
   INSERT INTO gmap_leads (nome, telefone, user_id, ...)
   │
   ▼
6. Backend Local envia status via WebSocket
   ws.emit('task_update', { progress, stats })
   │
   ▼
7. Frontend recebe atualização
   - Atualiza UI em tempo real
   - Mostra progresso
   │
   ▼
8. Quando termina:
   Frontend consulta Supabase diretamente
   supabase.from('gmap_leads').select('*')
   - RLS filtra por user_id automaticamente
```

## 🗂️ Onde Cada Dado Está

### SUPABASE (Dados Persistentes)
```
✅ users (perfis)
✅ gmap_leads (leads do Google Maps)
✅ facebook_ads_leads (leads do Facebook)
✅ email_results (emails extraídos)
✅ tasks (histórico de tarefas)
✅ email_dispatches (disparos de email)
✅ location_sets (conjuntos de locais)
✅ app_settings (configurações globais)
✅ storage/avatars (fotos de perfil)
```

### BACKEND LOCAL (Dados Temporários)
```
✅ Task manager (tasks em execução)
✅ WebSocket connections (clientes conectados)
✅ Worker state (estado dos scrapers)
✅ Cache temporário (se necessário)
```

### FRONTEND (Estado Local)
```
✅ Auth state (usuário logado)
✅ UI state (modais, filtros, etc)
✅ Cache de queries (React Query/Zustand)
✅ WebSocket connection (status de tasks)
```

## 🔄 Sincronização

### Frontend ↔ Supabase
```
- Realtime subscriptions (opcional)
- Polling (se necessário)
- Queries on-demand
- RLS automático
```

### Frontend ↔ Backend Local
```
- WebSocket para status de tasks
- HTTP para iniciar/parar automações
- Não armazena dados persistentes
```

### Backend Local ↔ Supabase
```
- INSERT de leads durante extração
- UPDATE de tasks
- Usa service_role key
- Inclui user_id manualmente
```

## 🎯 Vantagens desta Arquitetura

### 1. Segurança
- RLS do Supabase protege dados automaticamente
- Backend local não precisa gerenciar autenticação
- Token JWT validado em ambos os lados

### 2. Escalabilidade
- Supabase escala automaticamente
- Backend local pode ter múltiplas instâncias
- Cada usuário pode ter seu próprio backend local

### 3. Simplicidade
- Frontend fala diretamente com Supabase (CRUD)
- Backend local foca apenas em automações
- Menos código, menos bugs

### 4. Performance
- Queries diretas ao Supabase (sem proxy)
- WebSocket apenas para status (não dados)
- Cache no frontend (React Query)

## 🚫 O que NÃO fazer

### ❌ Backend Local como Proxy
```javascript
// ERRADO - Não fazer isso
fetch(`${backendUrl}/api/leads`)  // Backend local retorna leads

// CERTO - Fazer isso
supabase.from('gmap_leads').select('*')  // Direto no Supabase
```

### ❌ Autenticação no Backend Local
```python
# ERRADO - Backend local não gerencia auth
@router.post("/login")
async def login(email, password):
    # Não fazer isso!
    
# CERTO - Auth é 100% Supabase
# Backend local apenas VALIDA tokens
```

### ❌ Armazenar Dados no Backend Local
```python
# ERRADO - Não armazenar em SQLite/arquivo
leads = []  # Não fazer isso!

# CERTO - Sempre inserir no Supabase
supabase.table('gmap_leads').insert(lead).execute()
```

## ✅ O que FAZER

### ✅ Frontend → Supabase (Dados)
```javascript
// CRUD de leads
const { data } = await supabase.from('gmap_leads').select('*')
const { data } = await supabase.from('gmap_leads').insert(lead)
const { data } = await supabase.from('gmap_leads').update(lead)
const { data } = await supabase.from('gmap_leads').delete()

// Autenticação
await supabase.auth.signIn({ email, password })
await supabase.auth.signUp({ email, password })
await supabase.auth.signOut()

// Storage
await supabase.storage.from('avatars').upload(file)
```

### ✅ Frontend → Backend Local (Automações)
```javascript
// Iniciar extração
fetch(`${backendUrl}/api/gmap/start`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: JSON.stringify({ config })
})

// WebSocket para status
socket.on('task_update', (data) => {
  // Atualizar UI
})
```

### ✅ Backend Local → Supabase (Inserir Dados)
```python
# Durante extração, inserir leads
supabase.table('gmap_leads').insert({
    'nome': business_name,
    'telefone': phone,
    'user_id': user_id,  # Do token JWT
    'task_id': task_id,
    # ...
}).execute()
```

## 📝 Resumo

| Operação | Onde Acontece | Como |
|----------|---------------|------|
| Login/Cadastro | Supabase | Frontend → Supabase Auth |
| Ver Leads | Supabase | Frontend → Supabase DB (RLS) |
| Editar Lead | Supabase | Frontend → Supabase DB (RLS) |
| Deletar Lead | Supabase | Frontend → Supabase DB (RLS) |
| Upload Foto | Supabase | Frontend → Supabase Storage |
| Iniciar Extração | Backend Local | Frontend → FastAPI |
| Extrair Dados | Backend Local | Worker (Playwright) |
| Salvar Leads | Supabase | Backend Local → Supabase DB |
| Status em Tempo Real | Backend Local | WebSocket |

---

**Conclusão:** O Supabase é o backend real. O FastAPI local é apenas um worker de automações que insere dados no Supabase.
