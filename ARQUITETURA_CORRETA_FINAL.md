# ✅ Arquitetura Correta - Sistema Implementado

## 🎯 Princípio Fundamental

**SUPABASE = Backend Real**
**FastAPI Local = Worker de Automações**

## 📊 Fluxo de Dados Correto

```
┌──────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                       │
│                                                           │
│  ┌─────────────────────┐    ┌──────────────────────┐   │
│  │  Dados (CRUD)       │    │  Automações          │   │
│  │  - Leads            │    │  - Iniciar scraping  │   │
│  │  - Perfil           │    │  - Status tasks      │   │
│  │  - Auth             │    │  - Parar/Pausar      │   │
│  │  - Storage          │    │                      │   │
│  └──────┬──────────────┘    └──────┬───────────────┘   │
│         │                          │                    │
└─────────┼──────────────────────────┼────────────────────┘
          │                          │
          │ Supabase SDK             │ HTTP + WebSocket
          │ (direto)                 │
          │                          │
    ┌─────▼──────┐            ┌─────▼──────┐
    │            │            │            │
    │  SUPABASE  │◄───────────┤  FastAPI   │
    │            │  insere    │  Local     │
    │            │  dados     │            │
    └────────────┘            └────────────┘
```

## ✅ O que foi Implementado

### 1. Frontend → Supabase (DIRETO)

#### Arquivo: `frontend/src/services/supabase.js`
```javascript
// CRUD de leads - SEM passar pelo backend local
export const leadsService = {
  async getLeads() {
    return supabase.from('gmap_leads').select('*')
  },
  async updateLead(id, data) {
    return supabase.from('gmap_leads').update(data).eq('id', id)
  },
  async deleteLead(id) {
    return supabase.from('gmap_leads').delete().eq('id', id)
  }
}
```

#### Arquivo: `frontend/src/pages/LeadsPage.jsx`
```javascript
// Usa serviço do Supabase diretamente
import { leadsService } from '../services/supabase'

// Carrega leads
const { leads, total } = await leadsService.getLeads()

// Deleta lead
await leadsService.deleteLead(leadId)
```

### 2. Frontend → Backend Local (APENAS Automações)

#### Arquivo: `frontend/src/services/automation.js`
```javascript
// Apenas para iniciar/parar automações
export const automationService = {
  async startGMapExtraction(config) {
    const token = await getAuthToken()
    return fetch(`${backendUrl}/api/gmap/start`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: JSON.stringify(config)
    })
  }
}
```

### 3. Backend Local → Supabase (Inserir Dados)

#### Arquivo: `backend/modules/gmap/worker.py`
```python
# Worker extrai dados e insere no Supabase
async def extract_business(location, keyword, user_id):
    # 1. Playwright extrai dados do Google Maps
    business_data = await scrape_google_maps(location, keyword)
    
    # 2. Insere DIRETAMENTE no Supabase
    supabase.table('gmap_leads').insert({
        'nome': business_data['name'],
        'telefone': business_data['phone'],
        'user_id': user_id,  # Do token JWT
        'task_id': task_id,
        # ...
    }).execute()
```

## 🔄 Fluxos Completos

### Fluxo 1: Ver Leads (100% Supabase)
```
1. Usuário acessa /leads
2. Frontend chama leadsService.getLeads()
3. Supabase SDK faz query direta
4. RLS filtra por user_id automaticamente
5. Frontend exibe leads
```

### Fluxo 2: Editar Lead (100% Supabase)
```
1. Usuário edita lead
2. Frontend chama leadsService.updateLead(id, data)
3. Supabase SDK faz update direto
4. RLS valida que lead pertence ao usuário
5. Frontend atualiza UI
```

### Fluxo 3: Iniciar Extração (Backend Local + Supabase)
```
1. Usuário clica "Iniciar Extração"
2. Frontend chama automationService.startGMapExtraction()
3. Backend Local recebe requisição
4. Backend Local valida JWT token
5. Backend Local inicia worker (Playwright)
6. Worker extrai dados do Google Maps
7. Worker insere cada lead no Supabase (com user_id)
8. Backend Local envia status via WebSocket
9. Frontend atualiza UI em tempo real
10. Quando termina, frontend consulta Supabase diretamente
```

## 📁 Estrutura de Arquivos

### Frontend
```
frontend/src/
├── services/
│   ├── supabase.js          ← CRUD direto no Supabase
│   └── automation.js        ← Apenas automações
├── pages/
│   ├── LeadsPage.jsx        ← Usa supabase.js
│   ├── ProfilePage.jsx      ← Usa Supabase direto
│   └── LoginPage.jsx        ← Usa Supabase Auth
└── contexts/
    └── AuthContext.jsx      ← Usa Supabase Auth
```

### Backend
```
backend/
├── modules/
│   ├── gmap/
│   │   ├── router.py        ← Apenas start/stop
│   │   └── worker.py        ← Insere no Supabase
│   ├── facebook_ads/
│   │   ├── router.py        ← Apenas start/stop
│   │   └── worker.py        ← Insere no Supabase
│   └── leads/
│       └── router.py        ← NÃO USADO (frontend usa Supabase)
└── middleware/
    └── auth.py              ← Valida JWT para automações
```

## ❌ O que NÃO Fazer

### ❌ Backend Local como Proxy de Dados
```javascript
// ERRADO - Não fazer isso
fetch(`${backendUrl}/api/leads`)  // Backend retorna leads

// CERTO - Fazer isso
supabase.from('gmap_leads').select('*')  // Direto no Supabase
```

### ❌ Backend Local Gerenciar CRUD
```python
# ERRADO - Backend local não deve ter endpoints de CRUD
@router.get("/api/leads")
async def get_leads():
    # Não fazer isso!
    
# CERTO - Frontend faz direto no Supabase
# Backend local só tem endpoints de automação
```

## ✅ O que Fazer

### ✅ Frontend → Supabase (Dados)
```javascript
// Autenticação
await supabase.auth.signIn({ email, password })

// CRUD
const { data } = await supabase.from('gmap_leads').select('*')
await supabase.from('gmap_leads').insert(lead)
await supabase.from('gmap_leads').update(lead).eq('id', id)
await supabase.from('gmap_leads').delete().eq('id', id)

// Storage
await supabase.storage.from('avatars').upload(file)
```

### ✅ Frontend → Backend Local (Automações)
```javascript
// Iniciar extração
await automationService.startGMapExtraction(config)

// Parar task
await automationService.stopTask(taskId)

// WebSocket para status
socket.on('task_update', (data) => {
  // Atualizar UI
})
```

### ✅ Backend Local → Supabase (Inserir)
```python
# Worker insere dados durante extração
supabase.table('gmap_leads').insert({
    'nome': business_name,
    'user_id': user_id,  # Do JWT
    # ...
}).execute()
```

## 🎯 Benefícios desta Arquitetura

1. **Performance**: Queries diretas ao Supabase (sem proxy)
2. **Segurança**: RLS do Supabase protege dados automaticamente
3. **Simplicidade**: Menos código, menos bugs
4. **Escalabilidade**: Supabase escala automaticamente
5. **Flexibilidade**: Cada usuário pode ter seu próprio backend local

## 📝 Checklist de Implementação

- ✅ `frontend/src/services/supabase.js` criado
- ✅ `frontend/src/services/automation.js` criado
- ✅ `frontend/src/pages/LeadsPage.jsx` atualizado
- ✅ Backend local foca apenas em automações
- ✅ Workers inserem dados no Supabase
- ✅ RLS protege dados automaticamente

## 🚀 Próximos Passos

1. Atualizar outras páginas para usar `supabase.js`
2. Remover endpoints de CRUD do backend local
3. Garantir que workers incluem `user_id`
4. Testar fluxo completo

## 📖 Documentação

- `ARQUITETURA_REAL.md` - Arquitetura detalhada
- `frontend/src/services/supabase.js` - Serviço do Supabase
- `frontend/src/services/automation.js` - Serviço de automações

---

**Resumo:** Frontend fala DIRETAMENTE com Supabase para dados. Backend local é APENAS para automações.
