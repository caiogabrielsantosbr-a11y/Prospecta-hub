# ProspectaHub — Guia para Claude

## Identidade do projeto

**Nome:** ProspectaHub
**Descrição:** Plataforma de prospecção de leads unificada com integração a API local de scraping, gestão de leads e disparo de emails

**Repositório:** https://github.com/caiogabrielsantosbr-a11y/Prospecta-hub

---

## Arquitetura

```
Frontend (React/Vite)         → hospedado na Vercel
        ↓ JWT Auth
Backend FastAPI (local)       → roda na máquina do dev, exposto via ngrok
        ↓ Supabase SDK
Supabase (PostgreSQL + Auth + Storage + Edge Functions)   → cloud
```

O backend FastAPI **não está hospedado em produção** — roda localmente e é exposto via **ngrok** para que o frontend em produção (Vercel) consiga acessá-lo.

A URL do ngrok é configurada dinamicamente no frontend via painel admin (tabela `app_settings` no Supabase), sem necessidade de rebuild.

---

## Stack Completa

| Camada | Tecnologia |
|--------|-----------|
| Frontend framework | React 19 |
| Build tool | Vite 8 |
| Styling | TailwindCSS 4 |
| State management | Zustand 5 |
| Routing | react-router-dom 7 |
| Real-time | Socket.IO client 4.8 |
| Charts | Recharts 3 |
| Backend framework | FastAPI 0.115+ |
| Backend server | Uvicorn |
| ORM | SQLAlchemy 2.0 async |
| DB drivers | asyncpg (Postgres), aiosqlite (SQLite dev) |
| Scraping | Playwright 1.49 + BeautifulSoup4 |
| HTTP client | httpx |
| Cloud DB/Auth/Storage | Supabase |
| Edge Functions | Deno/TypeScript |
| Deploy frontend | Vercel |
| Tunnel dev | ngrok |

---

## Regras Obrigatórias de Edição (economizar tokens)

1. **NUNCA reescreva arquivos inteiros** — edite apenas o trecho necessário
2. **NUNCA explique o que foi feito após executar** — só execute
3. **NUNCA repita código já existente no contexto** — referencie por nome de função/arquivo
4. **Edições sempre cirúrgicas** — use Edit (str_replace) ou edição de bloco específico
5. **Se a tarefa não estiver clara, pergunte:** "Qual arquivo e qual comportamento exato?" antes de agir
6. Use `/clear` entre tarefas não relacionadas
7. **NUNCA decidir sozinho qual modelo usar** — seguir obrigatoriamente a tabela de modelos abaixo

---

## Tabela de Modelos — seguir sem exceção

| Tipo de tarefa | Modelo | Justificativa |
|---|---|---|
| Leitura de arquivos, edições simples, testes, operações Git, typos, formatação, ajustes de estilo | haiku | Custa 1/20 do Opus. Executa 90% das tarefas |
| Refatoração de múltiplos arquivos, nova feature, integração entre módulos, raciocínio sobre arquitetura | sonnet | Capacidade intermediária, custo moderado |
| Auditoria de segurança, depuração complexa, decisão arquitetural de alto impacto onde errar custa mais que os tokens | opus | Reservar apenas quando o custo de errar supera o custo do modelo |

### Regra de ouro dos modelos
- Padrão SEMPRE: **haiku**
- O modelo NUNCA é escolhido automaticamente — é definido pela tabela acima
- Só sobe para sonnet quando haiku claramente não resolve
- Opus é exceção rara — apenas quando errar custaria mais do que os tokens gastos

---

## Módulos do Projeto

| Módulo | Localização | Descrição |
|--------|------------|-----------|
| `api-client` | `frontend/src/services/api.js` | Chamadas fetch para API local de scraping (Google Maps, Facebook Ads, emails) |
| `leads` | `backend/modules/leads/`, `frontend/src/pages/LeadsPage.jsx` | Gestão de leads e conjuntos de localização |
| `campaigns` | `backend/modules/email_dispatch/`, `frontend/src/pages/EmailDispatchPage.jsx` | Disparo de emails SMTP |
| `gmail` | `backend/modules/gmail/`, `frontend/src/pages/InboxPage.jsx` + Edge Functions `gmail-accounts`, `gmail-messages`, `gmail-callback` | Inbox integrada, classificação Gemini, resposta automática |
| `admin` | `frontend/src/pages/AdminConfigPage.jsx`, `frontend/src/pages/ProfilePage.jsx` | Configuração ngrok URL, perfil de usuário, chave Gemini API |
| `gmap` | `backend/modules/gmap/`, `frontend/src/pages/GMapPage.jsx` | Scraping Google Maps via Playwright |
| `facebook` | `backend/modules/facebook_ads/`, `frontend/src/pages/FacebookAdsPage.jsx` | Scraping Facebook Ads |
| `emails` | `backend/modules/emails/`, `frontend/src/pages/EmailExtractorPage.jsx` | Extração de emails |
| `locations` | `backend/modules/locations/`, `frontend/src/pages/LocationSetsPage.jsx` | Conjuntos de localização para buscas |

---

## Estrutura de Pastas

```
Prospectahub/
├── backend/                  # FastAPI — Python 3.12
│   ├── main.py               # Entry point: CORS, health, dashboard stats
│   ├── requirements.txt
│   ├── .env / .env.example
│   ├── database/
│   │   ├── db.py             # SQLAlchemy async connection
│   │   ├── models.py         # ORM models
│   │   └── supabase_client.py  # Singleton Supabase client
│   ├── middleware/
│   │   └── auth.py           # JWT validation (Supabase tokens)
│   ├── modules/              # Feature modules (cada um tem router.py + worker.py)
│   │   ├── gmap/             # Google Maps scraping (Playwright)
│   │   ├── emails/           # Extração de emails
│   │   ├── email_dispatch/   # Disparo de emails (SMTP)
│   │   ├── facebook_ads/     # Facebook Ads scraping
│   │   ├── gmail/            # Gmail API (substituído por Edge Functions)
│   │   ├── leads/            # Gestão de leads
│   │   └── locations/        # Conjuntos de localização
│   ├── services/
│   │   ├── task_manager.py   # Background task management
│   │   └── csv_exporter.py   # Export CSV
│   ├── locais/               # JSONs com dados de localização do Brasil
│   └── data/                 # Runtime: exports, progress tracking
│
├── frontend/                 # React 19 + Vite + TailwindCSS
│   ├── src/
│   │   ├── App.jsx           # Root + routing
│   │   ├── config/supabase.js  # Supabase client init
│   │   ├── contexts/
│   │   │   ├── AuthContext.jsx   # Auth state global
│   │   │   └── ThemeContext.jsx  # Dark/light theme
│   │   ├── pages/            # Um arquivo por página
│   │   ├── components/       # Componentes reutilizáveis + layout/
│   │   ├── hooks/useWebSocket.js  # Socket.IO client
│   │   ├── services/
│   │   │   ├── api.js        # HTTP calls para o backend
│   │   │   ├── automation.js
│   │   │   └── supabase.js   # Operações diretas no Supabase
│   │   ├── store/
│   │   │   ├── useConfigStore.js  # Config global (Zustand, persiste no Supabase)
│   │   │   └── useTaskStore.js    # Estado de tasks
│   │   └── utils/sessionCache.js
│   ├── vite.config.js
│   └── .env / .env.example
│
├── Extensao appscript/       # Google Apps Script (GSheets integration)
│   ├── Code.gs               # Dispatcher + relatório diário
│   └── Sidebar.html
│
├── docs/                     # Documentação de referência
├── vercel.json               # Deploy config da Vercel
├── package.json              # Root: script "dev" (concurrently backend+frontend)
├── start.bat / start.sh      # Scripts para iniciar o dev server
└── CLAUDE.md                 # Este arquivo
```

---

## Páginas do Frontend

| Rota | Arquivo | Descrição |
|------|---------|-----------|
| `/` | Dashboard.jsx | Visão geral com stats |
| `/login` | LoginPage.jsx | Auth Supabase |
| `/profile` | ProfilePage.jsx | Perfil + upload avatar |
| `/gmap` | GMapPage.jsx | Scraping Google Maps |
| `/facebook` | FacebookAdsPage.jsx | Scraping Facebook Ads |
| `/emails` | EmailExtractorPage.jsx | Extração de emails |
| `/dispatch` | EmailDispatchPage.jsx | Campanha de email |
| `/leads` | LeadsPage.jsx | Gestão de leads + relatório diário |
| `/locations` | LocationSetsPage.jsx | Conjuntos de localização |
| `/inbox` | InboxPage.jsx | Gmail inbox integrada |
| `/admin` | AdminConfigPage.jsx | Config da URL do backend |
| `/auth/callback` | AuthCallbackPage.jsx | OAuth callback |

---

## Edge Functions Supabase (Deno/TypeScript)

| Função | verify_jwt | Descrição |
|--------|-----------|-----------|
| `gmail-accounts` | false | Listar/conectar/remover contas Gmail (OAuth2) |
| `gmail-messages` | false | Ler/listar mensagens, responder, classificar com Gemini |
| `gmail-callback` | false | Callback OAuth Google → salva tokens, fecha popup |

---

## Autenticação

- Supabase Auth (JWT)
- Frontend usa `AuthContext.jsx` + `@supabase/supabase-js`
- Backend valida JWT no `middleware/auth.py`
- Edge Functions: `verify_jwt: false` + validação interna via `supabase.auth.getUser(token)`
- Upload de avatar: Supabase Storage (bucket `avatars`)

---

## Supabase

- **Projeto ID:** `gyenypsxpidmsxabjhqg`
- **MCP configurado:** `.claude/settings.json` aponta para `mcp.supabase.com`
- Use `mcp__supabase__execute_sql` para queries diretas
- Use `mcp__supabase__list_tables` para ver schema

---

## Variáveis de Ambiente

### Backend (`backend/.env`)
```
DATABASE_URL=sqlite+aiosqlite:///./data/prospect.db
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
SMTP_FROM=
CORS_ORIGINS=http://localhost:5173,https://SEU-APP.vercel.app
SUPABASE_URL=https://SEU-PROJETO.supabase.co
SUPABASE_KEY=sua-anon-key
SUPABASE_JWT_SECRET=seu-jwt-secret
```

### Frontend (`frontend/.env`)
```
VITE_SUPABASE_URL=https://SEU-PROJETO.supabase.co
VITE_SUPABASE_KEY=sua-anon-key
```

### Supabase Secrets (Edge Functions)
```
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
GEMINI_API_KEY=   # fallback; usuário pode configurar o próprio via app_settings
```

---

## Como Rodar em Desenvolvimento

```bash
npm run setup   # setup inicial (uma vez)
npm run dev     # backend + frontend juntos
```

Para expor o backend via ngrok:
```bash
./ngrok.exe http 8000
# Copiar URL e colar no Admin Panel
```

---

## Estado Atual

- Auth (login, perfil, avatar) funcionando
- Gmail Inbox migrado para Edge Functions (OAuth2 + Gemini)
- Routers do backend comentados em `main.py` (debug temporário)
- Socket.IO temporariamente desabilitado
- Dashboard stats ainda mockado
- Location sets migrados para Supabase direto (sem depender do backend)

**Próximos passos:**
1. Reabilitar routers backend um a um
2. Reabilitar Socket.IO
3. Conectar dashboard stats ao Supabase real
4. Deploy do backend (Railway, Fly.io ou similar)

---

## LOG DE OTIMIZAÇÕES
