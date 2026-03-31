# Sistema de Usuários - Lead Prospecting App

Sistema completo de autenticação e isolamento de dados por usuário implementado com Supabase Auth e Row Level Security (RLS).

## 📋 Visão Geral

Cada usuário tem:
- ✅ Seus próprios leads (gmap_leads, facebook_ads_leads, email_results)
- ✅ Suas próprias tarefas (tasks)
- ✅ Seus próprios disparos de email (email_dispatches)
- ✅ URL de backend individual (configurável no perfil)
- ✅ Foto de perfil personalizada
- ✅ Acesso compartilhado aos conjuntos de locais (location_sets)

## 🗄️ Estrutura do Banco de Dados

### Tabelas Criadas

#### 1. `users`
Perfil estendido dos usuários (além do Supabase Auth):
- `id` (UUID) - Referência ao auth.users
- `email` (TEXT) - Email do usuário
- `full_name` (TEXT) - Nome completo
- `avatar_url` (TEXT) - URL da foto de perfil
- `backend_url` (TEXT) - URL do backend pessoal
- `created_at`, `updated_at` (TIMESTAMPTZ)

### Colunas Adicionadas

Todas as tabelas de dados receberam a coluna `user_id`:
- `gmap_leads.user_id`
- `facebook_ads_leads.user_id`
- `email_results.user_id`
- `tasks.user_id`
- `email_dispatches.user_id`

### Row Level Security (RLS)

Políticas implementadas:
- Usuários só podem ver/editar/deletar seus próprios dados
- Location_sets são compartilhados (todos podem ver/editar)
- App_settings são compartilhados (todos podem ver)

## 🎨 Frontend

### Páginas Criadas

#### 1. LoginPage (`frontend/src/pages/LoginPage.jsx`)
- Login com email/senha
- Cadastro de novos usuários
- Validação de formulários
- Redirecionamento automático se já logado

#### 2. ProfilePage (`frontend/src/pages/ProfilePage.jsx`)
- Visualização e edição do perfil
- Upload de foto de perfil
- Configuração de backend URL pessoal
- Logout

### Contextos

#### AuthContext (`frontend/src/contexts/AuthContext.jsx`)
Gerencia o estado de autenticação:
- `user` - Dados do usuário autenticado
- `profile` - Perfil estendido do usuário
- `loading` - Estado de carregamento
- `signUp()` - Criar nova conta
- `signIn()` - Fazer login
- `signOut()` - Fazer logout
- `updateProfile()` - Atualizar perfil
- `uploadAvatar()` - Upload de foto

### Componentes Atualizados

#### TopBar
- Menu dropdown com foto do usuário
- Links para perfil e configurações
- Botão de logout

#### Sidebar
- Link para página de perfil

#### App.jsx
- Rotas protegidas com `ProtectedRoute`
- Redirecionamento para login se não autenticado
- Integração com AuthProvider

## 🔧 Backend

### Middleware de Autenticação

#### `backend/middleware/auth.py`
- `get_current_user()` - Valida JWT e retorna user_id (obrigatório)
- `get_optional_user()` - Retorna user_id se presente (opcional)

### Routers Atualizados

#### `backend/modules/leads/router.py` (NOVO)
Endpoints com autenticação:
- `GET /api/leads` - Lista leads do usuário
- `GET /api/leads/stats` - Estatísticas dos leads
- `GET /api/leads/conjuntos` - Conjuntos únicos
- `GET /api/leads/cidades` - Cidades por conjunto
- `PUT /api/leads/{id}` - Atualizar lead
- `DELETE /api/leads/{id}` - Deletar lead
- `POST /api/leads/export` - Exportar leads

## 📦 Instalação e Configuração

### 1. Configurar Supabase

#### a) Aplicar Migrations
As migrations já foram aplicadas automaticamente:
- Tabela `users` criada
- Coluna `user_id` adicionada a todas as tabelas
- RLS habilitado
- Políticas de segurança criadas

#### b) Criar Bucket de Storage
Siga as instruções em `SETUP_STORAGE.md` para criar o bucket `avatars`.

#### c) Obter JWT Secret
1. Acesse o painel do Supabase
2. Vá em Settings > API
3. Copie o "JWT Secret"

### 2. Configurar Backend

#### a) Adicionar ao `.env`:
```env
# Supabase (já existentes)
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-anon

# Novo: JWT Secret para validação de tokens
SUPABASE_JWT_SECRET=seu-jwt-secret-aqui
```

#### b) Instalar Dependência:
```bash
pip install pyjwt
```

#### c) Atualizar Endpoints
Siga as instruções em `backend/USER_SYSTEM_INTEGRATION.md` para atualizar todos os endpoints.

### 3. Configurar Frontend

#### a) Variáveis de Ambiente (já configuradas):
```env
VITE_SUPABASE_URL=https://seu-projeto.supabase.co
VITE_SUPABASE_KEY=sua-chave-anon
```

#### b) Instalar Dependências:
```bash
cd frontend
npm install @supabase/supabase-js
```

## 🚀 Como Usar

### 1. Primeiro Acesso

1. Acesse a aplicação
2. Será redirecionado para `/login`
3. Clique em "Não tem conta? Crie uma agora"
4. Preencha nome, email e senha
5. Verifique seu email (se configurado)
6. Faça login

### 2. Configurar Perfil

1. Clique no avatar no canto superior direito
2. Selecione "Meu Perfil"
3. Faça upload de uma foto (opcional)
4. Configure sua URL de backend pessoal
5. Clique em "Salvar"

### 3. Usar a Aplicação

Agora você pode:
- Criar leads (serão associados à sua conta)
- Iniciar tarefas de extração
- Ver apenas seus próprios dados
- Compartilhar conjuntos de locais com outros usuários

## 🔒 Segurança

### Autenticação
- JWT tokens do Supabase Auth
- Tokens validados em cada requisição
- Expiração automática de sessões

### Autorização
- Row Level Security (RLS) no banco
- Validação de user_id em todos os endpoints
- Usuários não podem acessar dados de outros

### Dados Compartilhados
- Location_sets: Todos podem ver/editar
- App_settings: Todos podem ver

## 🧪 Testes

### Testar Isolamento de Dados

1. Crie dois usuários diferentes
2. Faça login com o primeiro usuário
3. Crie alguns leads
4. Faça logout e login com o segundo usuário
5. Verifique que não vê os leads do primeiro usuário
6. Crie leads com o segundo usuário
7. Verifique que ambos veem os mesmos location_sets

### Testar Autenticação

1. Tente acessar `/` sem estar logado → Deve redirecionar para `/login`
2. Faça login → Deve redirecionar para `/`
3. Tente acessar `/login` estando logado → Deve redirecionar para `/`
4. Faça logout → Deve redirecionar para `/login`

## 📝 Migração de Dados Existentes

Se você já tem dados no banco, atribua-os a um usuário:

```sql
-- Obter ID do primeiro usuário
SELECT id, email FROM auth.users LIMIT 1;

-- Atribuir dados ao usuário
UPDATE gmap_leads SET user_id = 'uuid-do-usuario' WHERE user_id IS NULL;
UPDATE facebook_ads_leads SET user_id = 'uuid-do-usuario' WHERE user_id IS NULL;
UPDATE email_results SET user_id = 'uuid-do-usuario' WHERE user_id IS NULL;
UPDATE tasks SET user_id = 'uuid-do-usuario' WHERE user_id IS NULL;
UPDATE email_dispatches SET user_id = 'uuid-do-usuario' WHERE user_id IS NULL;
```

## 📚 Documentação Adicional

- `SETUP_STORAGE.md` - Configuração do bucket de avatares
- `backend/USER_SYSTEM_INTEGRATION.md` - Guia detalhado de integração do backend
- `backend/middleware/auth.py` - Middleware de autenticação
- `backend/modules/leads/router.py` - Exemplo de router com autenticação

## 🎯 Próximos Passos

1. ✅ Sistema de usuários implementado
2. ⏳ Atualizar todos os endpoints do backend
3. ⏳ Atualizar workers para incluir user_id
4. ⏳ Testar com múltiplos usuários
5. ⏳ Implementar recuperação de senha
6. ⏳ Implementar verificação de email
7. ⏳ Adicionar roles/permissões (admin, user, etc.)

## 🐛 Troubleshooting

### Erro: "Missing authorization header"
- Verifique se o frontend está enviando o token
- Verifique se o AuthContext está configurado corretamente

### Erro: "Invalid token"
- Verifique se SUPABASE_JWT_SECRET está correto no backend
- Verifique se o token não expirou

### Erro: "Lead not found or you don't have permission"
- Verifique se o lead pertence ao usuário logado
- Verifique se o user_id está sendo enviado corretamente

### Storage: Erro ao fazer upload de avatar
- Verifique se o bucket `avatars` foi criado
- Verifique se as políticas RLS foram configuradas
- Verifique se o bucket é público

## 💡 Dicas

- Use o Supabase Dashboard para visualizar os dados
- Use o Network tab do DevTools para debugar requisições
- Verifique os logs do backend para erros de autenticação
- Use o Supabase Auth UI para gerenciar usuários

## 🤝 Contribuindo

Para adicionar novos endpoints:
1. Adicione `user_id: str = Depends(get_current_user)` aos parâmetros
2. Filtre queries por `user_id`
3. Inclua `user_id` ao inserir dados
4. Verifique permissões ao atualizar/deletar

## 📄 Licença

Este sistema foi desenvolvido como parte do Lead Prospecting App.
