# Prospectahub — Guia para Claude

## O que é esse projeto

**Prospectahub** (Plataforma Prospect) é uma plataforma de prospecção de leads unificada. Ela extrai leads de múltiplas fontes (Google Maps, Facebook Ads, extração de emails) e fornece ferramentas para gestão e disparo de emails.

**Repositório:** https://github.com/caiogabrielsantosbr-a11y/Prospecta-hub

---

## Arquitetura

```
Frontend (React/Vite)         → hospedado na Vercel
        ↓ JWT Auth
Backend FastAPI (local)       → roda na máquina do dev, exposto via ngrok
        ↓ Supabase SDK
Supabase (PostgreSQL + Auth + Storage)   → cloud
```

O backend FastAPI **não está hospedado em produção** — roda localmente e é exposto via **ngrok** para que o frontend em produção (Vercel) consiga acessá-lo.

A URL do ngrok é configurada dinamicamente no frontend via painel admin (tabela `app_settings` no Supabase), sem necessidade de rebuild.

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
├── docs/                     # Documentação de referência
├── vercel.json               # Deploy config da Vercel
├── package.json              # Root: script "dev" (concurrently backend+frontend)
├── start.bat / start.sh      # Scripts para iniciar o dev server
└── CLAUDE.md                 # Este arquivo
```

---

## Stack Técnica

| Camada | Tecnologia |
|--------|-----------|
| Frontend framework | React 19 |
| Build tool | Vite 8 |
| Styling | TailwindCSS 4 |
| State management | Zustand 5 |
| Routing | react-router-dom 7 |
| Real-time | Socket.IO (client 4.8) |
| Charts | Recharts 3 |
| Backend framework | FastAPI 0.115+ |
| Backend server | Uvicorn |
| ORM | SQLAlchemy 2.0 async |
| DB drivers | asyncpg (Postgres), aiosqlite (SQLite dev) |
| Scraping | Playwright 1.49 + BeautifulSoup4 |
| HTTP client | httpx |
| Cloud DB/Auth/Storage | Supabase |
| Deploy frontend | Vercel |
| Tunnel dev | ngrok |

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
| `/leads` | LeadsPage.jsx | Gestão de leads |
| `/locations` | LocationSetsPage.jsx | Conjuntos de localização |
| `/admin` | AdminConfigPage.jsx | Config da URL do backend |
| `/auth/callback` | AuthCallbackPage.jsx | OAuth callback |

---

## Endpoints do Backend

**ATENÇÃO:** A maioria dos routers está **comentada/desabilitada** em `main.py` (debug temporário). Só estão ativos:

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/health` | Health check |
| GET | `/api/dashboard/stats` | Estatísticas do dashboard (mock por enquanto) |

Routers disponíveis mas desabilitados (em `modules/`):
- `POST /api/emails/...` — extração de emails
- `GET/POST /api/gmap/...` — Google Maps scraping
- `GET/POST /api/facebook/...` — Facebook Ads
- `GET/POST /api/dispatch/...` — disparo de email
- `GET/POST /api/locations/...` — location sets
- `GET /api/leads/...` — leads

---

## Modelos do Banco de Dados (SQLAlchemy ORM)

| Modelo | Tabela | Descrição |
|--------|--------|-----------|
| `GMapLead` | `gmap_leads` | Leads do Google Maps |
| `FacebookAdsLead` | `facebook_ads_leads` | Leads do Facebook |
| `EmailResult` | `email_results` | Emails extraídos |
| `TaskRecord` | `task_records` | Histórico de tasks |
| `EmailDispatch` | `email_dispatches` | Fila de disparo |
| `DMTemplate` | `dm_templates` | Templates de DM |
| `ApproachScript` | `approach_scripts` | Scripts de abordagem |

Tabela Supabase adicional:
- `app_settings` — configurações globais (URL do backend, etc.)

---

## Autenticação

- Supabase Auth (JWT)
- Frontend usa `AuthContext.jsx` + `@supabase/supabase-js`
- Backend valida JWT no `middleware/auth.py`
- Upload de avatar: Supabase Storage (bucket `avatars`)

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

---

## Como Rodar em Desenvolvimento

```bash
# Setup inicial (uma vez)
npm run setup

# Iniciar tudo (backend + frontend juntos)
npm run dev

# Ou separados
npm run dev:backend   # FastAPI em localhost:8000
npm run dev:frontend  # React/Vite em localhost:5173
```

Para expor o backend localmente via ngrok:
```bash
./ngrok.exe http 8000
# Copiar a URL gerada e colar no Admin Panel do frontend
```

---

## Deploy

- **Frontend:** Vercel — config em `vercel.json`
  - Build: `cd frontend && npm run build`
  - Output: `frontend/dist/`
  - Rewrites para SPA: `"source": "/(.*)" → "/index.html"`
- **Backend:** Roda localmente + ngrok (não há deploy em cloud atualmente)

---

## Estado Atual do Projeto

O backend está em fase de estabilização. Os routers estão comentados em `main.py` para debug. O fluxo principal de auth (login, perfil, avatar) já funciona. As features de scraping (GMap, Facebook) precisam ter os routers reabilitados e testados.

**Próximos passos prováveis:**
1. Reabilitar routers um a um e testar
2. Reabilitar Socket.IO para updates em tempo real
3. Conectar dashboard stats ao Supabase real
4. Configurar deploy do backend (Railway, Fly.io, ou similar)

---

## Supabase

- **Projeto ID:** `gyenypsxpidmsxabjhqg`
- **MCP configurado:** `.claude/settings.json` aponta para `mcp.supabase.com`
- Use `mcp__supabase__execute_sql` para queries diretas
- Use `mcp__supabase__list_tables` para ver schema

---

## Notas Importantes

- O `DATABASE_URL` usa **SQLite** por padrão (dev local), mas o objetivo é usar o **Supabase PostgreSQL** via `supabase_client.py`
- Socket.IO está temporariamente desabilitado em `main.py` (comentado para debug)
- `TaskManagerBar.jsx` no frontend ainda referencia o sistema de tasks que está desabilitado
- O arquivo `start.bat` / `start.sh` é o jeito mais fácil de subir o ambiente
