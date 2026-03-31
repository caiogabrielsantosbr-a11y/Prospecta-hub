# Integração do Sistema de Usuários no Backend

Este documento descreve as mudanças necessárias para integrar o sistema de usuários no backend.

## 1. Variáveis de Ambiente

Adicione ao arquivo `.env`:

```env
# Supabase JWT Secret (encontre em: Settings > API > JWT Secret)
SUPABASE_JWT_SECRET=your-jwt-secret-here
```

## 2. Middleware de Autenticação

O middleware de autenticação foi criado em `backend/middleware/auth.py` e fornece:

- `get_current_user()`: Extrai e valida o user_id do token JWT (obrigatório)
- `get_optional_user()`: Extrai user_id se presente, senão retorna None (opcional)

## 3. Atualização dos Endpoints

Todos os endpoints que manipulam dados do usuário devem ser atualizados para:

### 3.1. Adicionar Dependência de Autenticação

```python
from fastapi import Depends
from middleware.auth import get_current_user

@router.post("/api/leads")
async def create_lead(
    lead_data: dict,
    user_id: str = Depends(get_current_user)
):
    # user_id agora está disponível
    lead_data['user_id'] = user_id
    # ... resto do código
```

### 3.2. Filtrar Dados por user_id

Ao buscar dados do Supabase, sempre filtre por user_id:

```python
# Antes
response = supabase.table('gmap_leads').select('*').execute()

# Depois
response = supabase.table('gmap_leads')\
    .select('*')\
    .eq('user_id', user_id)\
    .execute()
```

### 3.3. Incluir user_id ao Inserir Dados

```python
# Antes
data = {
    'nome': lead.nome,
    'telefone': lead.telefone,
    # ...
}

# Depois
data = {
    'nome': lead.nome,
    'telefone': lead.telefone,
    'user_id': user_id,  # ← Adicionar
    # ...
}
```

## 4. Endpoints que Precisam ser Atualizados

### 4.1. GMap Module (`backend/modules/gmap/router.py`)

- `POST /api/gmap/start` - Adicionar user_id ao criar task
- `GET /api/gmap/leads` - Filtrar leads por user_id
- `POST /api/gmap/leads` - Incluir user_id ao inserir lead

### 4.2. Facebook Ads Module (`backend/modules/facebook_ads/router.py`)

- `POST /api/facebook/start` - Adicionar user_id ao criar task
- `GET /api/facebook/leads` - Filtrar leads por user_id
- `POST /api/facebook/leads` - Incluir user_id ao inserir lead

### 4.3. Email Dispatch Module (`backend/modules/email_dispatch/router.py`)

- `POST /api/dispatch/start` - Adicionar user_id ao criar task
- `GET /api/dispatch/history` - Filtrar dispatches por user_id
- `POST /api/dispatch/send` - Incluir user_id ao criar dispatch

### 4.4. Leads Module (`backend/modules/leads/router.py` - se existir)

- `GET /api/leads` - Filtrar por user_id
- `GET /api/leads/stats` - Calcular stats apenas para user_id
- `PUT /api/leads/{id}` - Verificar se lead pertence ao user_id
- `DELETE /api/leads/{id}` - Verificar se lead pertence ao user_id
- `POST /api/leads/export` - Exportar apenas leads do user_id

### 4.5. Tasks Module

- `GET /api/tasks` - Filtrar tasks por user_id
- `GET /api/tasks/{id}` - Verificar se task pertence ao user_id
- `PUT /api/tasks/{id}` - Verificar se task pertence ao user_id
- `DELETE /api/tasks/{id}` - Verificar se task pertence ao user_id

## 5. Endpoints Compartilhados (Sem Filtro de user_id)

Estes endpoints devem permanecer acessíveis a todos os usuários autenticados:

### 5.1. Location Sets

- `GET /api/location-sets` - Todos podem ver
- `POST /api/location-sets` - Todos podem criar
- `PUT /api/location-sets/{id}` - Todos podem editar
- `DELETE /api/location-sets/{id}` - Todos podem deletar

### 5.2. App Settings

- `GET /api/settings` - Todos podem ver (mas cada usuário tem seu backend_url no perfil)

## 6. Workers e Background Tasks

Os workers também precisam incluir user_id ao inserir dados:

### 6.1. GMap Worker (`backend/modules/gmap/worker.py`)

```python
# Ao inserir lead no Supabase
lead_data = {
    'nome': business_name,
    'telefone': phone,
    'website': website,
    'endereco': address,
    'cidade': city,
    'url': url,
    'conjunto_de_locais': location_set_name,
    'task_id': task_id,
    'user_id': user_id,  # ← Adicionar
}
```

### 6.2. Facebook Ads Worker (`backend/modules/facebook_ads/worker.py`)

Similar ao GMap Worker, incluir user_id ao inserir leads.

### 6.3. Email Dispatch Worker (`backend/modules/email_dispatch/worker.py`)

Incluir user_id ao criar registros de dispatch.

## 7. Exemplo Completo de Endpoint Atualizado

```python
from fastapi import APIRouter, Depends, HTTPException
from middleware.auth import get_current_user
from database.supabase_client import SupabaseClient

router = APIRouter()
supabase = SupabaseClient()

@router.get("/api/leads")
async def get_leads(
    limit: int = 50,
    offset: int = 0,
    user_id: str = Depends(get_current_user)
):
    """Get leads for the authenticated user"""
    try:
        response = supabase.client\
            .table('gmap_leads')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        return {
            'leads': response.data,
            'total': len(response.data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/leads")
async def create_lead(
    lead_data: dict,
    user_id: str = Depends(get_current_user)
):
    """Create a new lead for the authenticated user"""
    try:
        # Add user_id to lead data
        lead_data['user_id'] = user_id
        
        response = supabase.client\
            .table('gmap_leads')\
            .insert(lead_data)\
            .execute()
        
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/leads/{lead_id}")
async def delete_lead(
    lead_id: int,
    user_id: str = Depends(get_current_user)
):
    """Delete a lead (only if it belongs to the user)"""
    try:
        # First check if lead belongs to user
        check = supabase.client\
            .table('gmap_leads')\
            .select('id')\
            .eq('id', lead_id)\
            .eq('user_id', user_id)\
            .execute()
        
        if not check.data:
            raise HTTPException(
                status_code=404,
                detail="Lead not found or you don't have permission"
            )
        
        # Delete the lead
        supabase.client\
            .table('gmap_leads')\
            .delete()\
            .eq('id', lead_id)\
            .execute()
        
        return {'message': 'Lead deleted successfully'}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## 8. Frontend - Envio do Token

O frontend já está configurado para enviar o token automaticamente através do AuthContext.

Para fazer requisições autenticadas, o frontend deve incluir o header:

```javascript
const { user } = useAuth()
const session = await supabase.auth.getSession()
const token = session.data.session?.access_token

fetch(`${apiUrl}/api/leads`, {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
```

## 9. Testes

Após implementar as mudanças:

1. Crie dois usuários diferentes
2. Crie leads com cada usuário
3. Verifique que cada usuário vê apenas seus próprios leads
4. Verifique que ambos podem ver os mesmos location_sets

## 10. Migração de Dados Existentes

Se você já tem dados no banco, precisará atribuí-los a um usuário:

```sql
-- Atribuir todos os leads existentes a um usuário específico
UPDATE gmap_leads 
SET user_id = 'uuid-do-usuario' 
WHERE user_id IS NULL;

UPDATE facebook_ads_leads 
SET user_id = 'uuid-do-usuario' 
WHERE user_id IS NULL;

UPDATE email_results 
SET user_id = 'uuid-do-usuario' 
WHERE user_id IS NULL;

UPDATE tasks 
SET user_id = 'uuid-do-usuario' 
WHERE user_id IS NULL;

UPDATE email_dispatches 
SET user_id = 'uuid-do-usuario' 
WHERE user_id IS NULL;
```

## 11. Próximos Passos

1. Adicionar `SUPABASE_JWT_SECRET` ao `.env`
2. Atualizar todos os endpoints conforme descrito
3. Atualizar os workers para incluir user_id
4. Testar com múltiplos usuários
5. Criar documentação de API atualizada
