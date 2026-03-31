# 🔧 Debug e Manutenção - Sistema de Usuários

## 🐛 Comandos de Debug

### Verificar Usuários no Banco

```sql
-- Ver todos os usuários
SELECT id, email, full_name, backend_url, created_at 
FROM users 
ORDER BY created_at DESC;

-- Ver usuário específico
SELECT * FROM users WHERE email = 'usuario@email.com';

-- Contar usuários
SELECT COUNT(*) as total_usuarios FROM users;
```

### Verificar Leads por Usuário

```sql
-- Ver leads de um usuário específico
SELECT id, nome, telefone, user_id, created_at 
FROM gmap_leads 
WHERE user_id = 'uuid-do-usuario'
ORDER BY created_at DESC;

-- Contar leads por usuário
SELECT 
    u.email,
    u.full_name,
    COUNT(g.id) as total_leads
FROM users u
LEFT JOIN gmap_leads g ON g.user_id = u.id
GROUP BY u.id, u.email, u.full_name
ORDER BY total_leads DESC;

-- Ver leads sem user_id (dados órfãos)
SELECT COUNT(*) as leads_sem_usuario 
FROM gmap_leads 
WHERE user_id IS NULL;
```

### Verificar RLS

```sql
-- Ver políticas RLS ativas
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual
FROM pg_policies
WHERE tablename IN ('gmap_leads', 'users', 'location_sets')
ORDER BY tablename, policyname;

-- Verificar se RLS está habilitado
SELECT 
    schemaname,
    tablename,
    rowsecurity
FROM pg_tables
WHERE tablename IN ('gmap_leads', 'facebook_ads_leads', 'users', 'location_sets')
ORDER BY tablename;
```

### Verificar Storage

```sql
-- Ver arquivos no storage
SELECT 
    name,
    bucket_id,
    owner,
    created_at,
    metadata
FROM storage.objects
WHERE bucket_id = 'avatars'
ORDER BY created_at DESC;

-- Contar arquivos por usuário
SELECT 
    owner,
    COUNT(*) as total_arquivos
FROM storage.objects
WHERE bucket_id = 'avatars'
GROUP BY owner;
```

## 🔍 Debug no Frontend

### Console do Navegador

```javascript
// Ver usuário atual
const { data: { user } } = await supabase.auth.getUser()
console.log('Usuário:', user)

// Ver sessão atual
const { data: { session } } = await supabase.auth.getSession()
console.log('Sessão:', session)
console.log('Token:', session?.access_token)

// Decodificar token JWT (sem validar)
const token = session?.access_token
const payload = JSON.parse(atob(token.split('.')[1]))
console.log('Payload do token:', payload)

// Ver perfil do usuário
const { data: profile } = await supabase
  .from('users')
  .select('*')
  .eq('id', user.id)
  .single()
console.log('Perfil:', profile)

// Testar query com RLS
const { data: leads, error } = await supabase
  .from('gmap_leads')
  .select('*')
  .limit(10)
console.log('Leads:', leads)
console.log('Erro:', error)
```

### DevTools Network

```
1. Abrir DevTools (F12)
2. Ir para aba Network
3. Fazer uma requisição
4. Clicar na requisição
5. Ver Headers:
   - Authorization: Bearer <token>
6. Ver Response:
   - Dados retornados
   - Erros
```

### LocalStorage

```javascript
// Ver dados armazenados
console.log('LocalStorage:', localStorage)

// Ver token do Supabase
const supabaseData = localStorage.getItem('sb-<project-ref>-auth-token')
console.log('Supabase Auth:', JSON.parse(supabaseData))

// Limpar cache
localStorage.clear()
sessionStorage.clear()
```

## 🔧 Debug no Backend

### Logs do Backend

```python
# Adicionar logs temporários
import logging
logger = logging.getLogger(__name__)

# No endpoint
@router.get("/api/leads")
async def get_leads(user_id: str = Depends(get_current_user)):
    logger.info(f"User {user_id} requesting leads")
    # ... resto do código
    logger.info(f"Returning {len(leads)} leads")
```

### Testar Middleware

```python
# Testar validação de token
from middleware.auth import get_current_user

# Token válido
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
try:
    user_id = get_current_user(f"Bearer {token}")
    print(f"User ID: {user_id}")
except Exception as e:
    print(f"Erro: {e}")
```

### Testar Endpoint com cURL

```bash
# Obter token (fazer login primeiro e copiar do DevTools)
TOKEN="seu-token-aqui"

# Testar endpoint
curl -X GET "http://localhost:8000/api/leads" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# Testar com token inválido
curl -X GET "http://localhost:8000/api/leads" \
  -H "Authorization: Bearer token-invalido" \
  -H "Content-Type: application/json"

# Testar sem token
curl -X GET "http://localhost:8000/api/leads" \
  -H "Content-Type: application/json"
```

## 🛠️ Comandos de Manutenção

### Migrar Dados Existentes

```sql
-- Criar um usuário admin para dados órfãos
-- (Primeiro, criar o usuário via interface)

-- Atribuir leads órfãos ao admin
UPDATE gmap_leads 
SET user_id = 'uuid-do-admin' 
WHERE user_id IS NULL;

UPDATE facebook_ads_leads 
SET user_id = 'uuid-do-admin' 
WHERE user_id IS NULL;

UPDATE email_results 
SET user_id = 'uuid-do-admin' 
WHERE user_id IS NULL;

UPDATE tasks 
SET user_id = 'uuid-do-admin' 
WHERE user_id IS NULL;

UPDATE email_dispatches 
SET user_id = 'uuid-do-admin' 
WHERE user_id IS NULL;
```

### Limpar Dados de Teste

```sql
-- Deletar usuário de teste e todos seus dados
-- (RLS com ON DELETE CASCADE faz isso automaticamente)
DELETE FROM auth.users WHERE email = 'teste@email.com';

-- Ou deletar apenas os leads
DELETE FROM gmap_leads WHERE user_id = 'uuid-do-usuario-teste';
```

### Resetar Senha de Usuário

```javascript
// No console do navegador ou via código
const { data, error } = await supabase.auth.resetPasswordForEmail(
  'usuario@email.com',
  {
    redirectTo: 'http://localhost:5173/reset-password',
  }
)
```

### Verificar Integridade dos Dados

```sql
-- Verificar leads sem usuário
SELECT COUNT(*) FROM gmap_leads WHERE user_id IS NULL;

-- Verificar usuários sem perfil
SELECT u.id, u.email 
FROM auth.users u
LEFT JOIN users p ON p.id = u.id
WHERE p.id IS NULL;

-- Verificar perfis sem usuário (órfãos)
SELECT p.id, p.email 
FROM users p
LEFT JOIN auth.users u ON u.id = p.id
WHERE u.id IS NULL;
```

## 🔐 Segurança

### Verificar Políticas RLS

```sql
-- Testar se RLS está funcionando
-- (Execute como usuário específico)

-- Deve retornar apenas leads do usuário
SELECT * FROM gmap_leads;

-- Deve retornar todos os location_sets
SELECT * FROM location_sets;
```

### Verificar Tokens Expirados

```javascript
// No console do navegador
const { data: { session } } = await supabase.auth.getSession()
if (session) {
  const expiresAt = new Date(session.expires_at * 1000)
  const now = new Date()
  const timeLeft = expiresAt - now
  
  console.log('Token expira em:', expiresAt)
  console.log('Tempo restante:', Math.floor(timeLeft / 1000 / 60), 'minutos')
  
  if (timeLeft < 0) {
    console.log('Token expirado!')
  }
}
```

### Revogar Sessões

```javascript
// Fazer logout de todas as sessões
await supabase.auth.signOut({ scope: 'global' })

// Fazer logout apenas da sessão atual
await supabase.auth.signOut({ scope: 'local' })
```

## 📊 Monitoramento

### Estatísticas de Uso

```sql
-- Usuários mais ativos (por número de leads)
SELECT 
    u.email,
    u.full_name,
    COUNT(g.id) as total_leads,
    MAX(g.created_at) as ultimo_lead
FROM users u
LEFT JOIN gmap_leads g ON g.user_id = u.id
GROUP BY u.id, u.email, u.full_name
ORDER BY total_leads DESC
LIMIT 10;

-- Novos usuários por dia
SELECT 
    DATE(created_at) as data,
    COUNT(*) as novos_usuarios
FROM users
GROUP BY DATE(created_at)
ORDER BY data DESC
LIMIT 30;

-- Leads criados por dia
SELECT 
    DATE(created_at) as data,
    COUNT(*) as novos_leads
FROM gmap_leads
GROUP BY DATE(created_at)
ORDER BY data DESC
LIMIT 30;
```

### Performance

```sql
-- Verificar índices
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('gmap_leads', 'users', 'tasks')
ORDER BY tablename, indexname;

-- Verificar tamanho das tabelas
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## 🧪 Testes Automatizados

### Script de Teste Python

```python
import requests
import json

BASE_URL = "http://localhost:8000"
TOKEN = "seu-token-aqui"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Testar endpoint de leads
response = requests.get(f"{BASE_URL}/api/leads", headers=headers)
print(f"Status: {response.status_code}")
print(f"Leads: {len(response.json()['leads'])}")

# Testar sem token
response = requests.get(f"{BASE_URL}/api/leads")
print(f"Sem token - Status: {response.status_code}")
assert response.status_code == 401, "Deveria retornar 401"

# Testar com token inválido
bad_headers = {"Authorization": "Bearer token-invalido"}
response = requests.get(f"{BASE_URL}/api/leads", headers=bad_headers)
print(f"Token inválido - Status: {response.status_code}")
assert response.status_code == 401, "Deveria retornar 401"

print("✅ Todos os testes passaram!")
```

### Script de Teste JavaScript

```javascript
// test-auth.js
const { createClient } = require('@supabase/supabase-js')

const supabase = createClient(
  process.env.VITE_SUPABASE_URL,
  process.env.VITE_SUPABASE_KEY
)

async function testAuth() {
  // Criar usuário de teste
  const { data: signUpData, error: signUpError } = await supabase.auth.signUp({
    email: 'teste@email.com',
    password: 'senha123'
  })
  
  if (signUpError) {
    console.error('Erro ao criar usuário:', signUpError)
    return
  }
  
  console.log('✅ Usuário criado')
  
  // Fazer login
  const { data: signInData, error: signInError } = await supabase.auth.signInWithPassword({
    email: 'teste@email.com',
    password: 'senha123'
  })
  
  if (signInError) {
    console.error('Erro ao fazer login:', signInError)
    return
  }
  
  console.log('✅ Login realizado')
  
  // Verificar perfil
  const { data: profile, error: profileError } = await supabase
    .from('users')
    .select('*')
    .eq('id', signInData.user.id)
    .single()
  
  if (profileError) {
    console.error('Erro ao buscar perfil:', profileError)
    return
  }
  
  console.log('✅ Perfil encontrado:', profile)
  
  // Limpar
  await supabase.auth.signOut()
  console.log('✅ Logout realizado')
}

testAuth()
```

## 🚨 Troubleshooting

### Problema: Token inválido

```bash
# Verificar JWT_SECRET
echo $SUPABASE_JWT_SECRET

# Deve ser o mesmo do Supabase Dashboard
# Settings > API > JWT Secret
```

### Problema: RLS bloqueando queries

```sql
-- Desabilitar RLS temporariamente (APENAS PARA DEBUG)
ALTER TABLE gmap_leads DISABLE ROW LEVEL SECURITY;

-- Testar query
SELECT * FROM gmap_leads;

-- Reabilitar RLS
ALTER TABLE gmap_leads ENABLE ROW LEVEL SECURITY;
```

### Problema: Usuário não consegue ver seus dados

```sql
-- Verificar se user_id está correto
SELECT id, nome, user_id FROM gmap_leads WHERE id = 123;

-- Verificar se usuário existe
SELECT id, email FROM users WHERE id = 'uuid-do-usuario';

-- Verificar políticas RLS
SELECT * FROM pg_policies WHERE tablename = 'gmap_leads';
```

### Problema: Upload de avatar falha

```sql
-- Verificar bucket
SELECT * FROM storage.buckets WHERE id = 'avatars';

-- Verificar políticas do storage
SELECT * FROM storage.policies WHERE bucket_id = 'avatars';

-- Verificar se bucket é público
SELECT id, name, public FROM storage.buckets WHERE id = 'avatars';
```

## 📝 Logs Úteis

### Backend

```python
# Adicionar ao início do arquivo
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Logs úteis
logger.debug(f"User ID: {user_id}")
logger.info(f"Query returned {len(results)} results")
logger.warning(f"Slow query: {elapsed_time}s")
logger.error(f"Error: {str(e)}")
```

### Frontend

```javascript
// Habilitar logs do Supabase
const supabase = createClient(url, key, {
  auth: {
    debug: true
  }
})

// Logs úteis
console.log('User:', user)
console.log('Profile:', profile)
console.log('Token:', session?.access_token)
console.error('Error:', error)
```

---

📖 **Documentação Completa**: `USER_SYSTEM_README.md`
🏗️ **Arquitetura**: `ARQUITETURA_SISTEMA_USUARIOS.md`
🧪 **Testes**: `TEST_USER_SYSTEM.md`
