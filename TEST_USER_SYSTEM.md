# Checklist de Testes - Sistema de Usuários

Use este checklist para verificar se o sistema de usuários está funcionando corretamente.

## ✅ Pré-requisitos

- [ ] Supabase configurado com as migrations aplicadas
- [ ] Bucket `avatars` criado no Supabase Storage
- [ ] `SUPABASE_JWT_SECRET` adicionado ao `.env` do backend
- [ ] Dependência `pyjwt` instalada no backend
- [ ] Frontend e backend rodando

## 🧪 Testes de Autenticação

### 1. Cadastro de Usuário
- [ ] Acessar `/login`
- [ ] Clicar em "Não tem conta? Crie uma agora"
- [ ] Preencher nome, email e senha
- [ ] Clicar em "Criar Conta"
- [ ] Verificar mensagem de sucesso
- [ ] Verificar se foi redirecionado para `/` (ou se precisa verificar email)

### 2. Login
- [ ] Acessar `/login`
- [ ] Preencher email e senha
- [ ] Clicar em "Entrar"
- [ ] Verificar mensagem de sucesso
- [ ] Verificar se foi redirecionado para `/`

### 3. Proteção de Rotas
- [ ] Fazer logout
- [ ] Tentar acessar `/` → Deve redirecionar para `/login`
- [ ] Tentar acessar `/leads` → Deve redirecionar para `/login`
- [ ] Tentar acessar `/profile` → Deve redirecionar para `/login`
- [ ] Fazer login
- [ ] Tentar acessar `/login` → Deve redirecionar para `/`

### 4. Logout
- [ ] Clicar no avatar no canto superior direito
- [ ] Clicar em "Sair"
- [ ] Verificar mensagem de sucesso
- [ ] Verificar se foi redirecionado para `/login`

## 👤 Testes de Perfil

### 1. Visualização do Perfil
- [ ] Fazer login
- [ ] Clicar no avatar no canto superior direito
- [ ] Clicar em "Meu Perfil"
- [ ] Verificar se nome e email estão corretos
- [ ] Verificar se data de criação está correta

### 2. Edição do Perfil
- [ ] Na página de perfil, clicar em "Editar"
- [ ] Alterar o nome
- [ ] Alterar a URL do backend
- [ ] Clicar em "Salvar"
- [ ] Verificar mensagem de sucesso
- [ ] Recarregar a página
- [ ] Verificar se as alterações foram salvas

### 3. Upload de Avatar
- [ ] Na página de perfil, clicar em "Alterar Foto"
- [ ] Selecionar uma imagem (PNG, JPG, etc.)
- [ ] Verificar mensagem de sucesso
- [ ] Verificar se a foto aparece no perfil
- [ ] Verificar se a foto aparece no TopBar
- [ ] Recarregar a página
- [ ] Verificar se a foto persiste

### 4. Validações
- [ ] Tentar fazer upload de arquivo não-imagem → Deve mostrar erro
- [ ] Tentar fazer upload de imagem > 2MB → Deve mostrar erro

## 🔒 Testes de Isolamento de Dados

### 1. Criar Dois Usuários
- [ ] Criar usuário A (email1@test.com)
- [ ] Criar usuário B (email2@test.com)

### 2. Testar Isolamento de Leads
- [ ] Fazer login com usuário A
- [ ] Criar 3 leads manualmente ou via extração
- [ ] Verificar que os 3 leads aparecem em `/leads`
- [ ] Fazer logout
- [ ] Fazer login com usuário B
- [ ] Verificar que `/leads` está vazio (não mostra leads do usuário A)
- [ ] Criar 2 leads
- [ ] Verificar que apenas os 2 leads do usuário B aparecem
- [ ] Fazer logout
- [ ] Fazer login com usuário A
- [ ] Verificar que ainda vê apenas seus 3 leads originais

### 3. Testar Isolamento de Tarefas
- [ ] Fazer login com usuário A
- [ ] Iniciar uma tarefa de extração
- [ ] Verificar que a tarefa aparece no TaskManagerBar
- [ ] Fazer logout
- [ ] Fazer login com usuário B
- [ ] Verificar que não vê a tarefa do usuário A
- [ ] Iniciar uma tarefa própria
- [ ] Verificar que vê apenas sua tarefa

### 4. Testar Compartilhamento de Location Sets
- [ ] Fazer login com usuário A
- [ ] Ir para a página de Location Sets (se existir)
- [ ] Criar um conjunto "Teste Compartilhado"
- [ ] Fazer logout
- [ ] Fazer login com usuário B
- [ ] Verificar que vê o conjunto "Teste Compartilhado"
- [ ] Editar o conjunto
- [ ] Fazer logout
- [ ] Fazer login com usuário A
- [ ] Verificar que vê as edições do usuário B

## 🔐 Testes de Segurança

### 1. Tentativa de Acesso Não Autorizado
- [ ] Fazer login com usuário A
- [ ] Abrir DevTools > Network
- [ ] Criar um lead
- [ ] Copiar o ID do lead da resposta
- [ ] Fazer logout
- [ ] Fazer login com usuário B
- [ ] Tentar deletar o lead do usuário A via API:
  ```javascript
  // No console do navegador
  const session = await supabase.auth.getSession()
  const token = session.data.session?.access_token
  
  fetch('http://localhost:8000/api/leads/ID_DO_LEAD_DO_USUARIO_A', {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  })
  ```
- [ ] Verificar que retorna erro 404 (não encontrado)
- [ ] Fazer login com usuário A
- [ ] Verificar que o lead ainda existe

### 2. Validação de Token
- [ ] Fazer login
- [ ] Abrir DevTools > Application > Local Storage
- [ ] Encontrar o token do Supabase
- [ ] Modificar o token (alterar alguns caracteres)
- [ ] Tentar acessar `/leads`
- [ ] Verificar que é redirecionado para `/login`

## 📊 Testes de Estatísticas

### 1. Stats por Usuário
- [ ] Fazer login com usuário A
- [ ] Criar 5 leads (3 com telefone, 2 sem telefone)
- [ ] Ir para `/leads`
- [ ] Verificar que as estatísticas mostram:
  - Total: 5
  - Com telefone: 3
  - Sem telefone: 2
- [ ] Fazer logout
- [ ] Fazer login com usuário B
- [ ] Verificar que as estatísticas estão zeradas ou mostram apenas dados do usuário B

## 🎨 Testes de UI

### 1. TopBar
- [ ] Verificar que o avatar aparece no canto superior direito
- [ ] Verificar que o nome do usuário aparece ao lado do avatar
- [ ] Clicar no avatar
- [ ] Verificar que o menu dropdown abre
- [ ] Verificar que mostra nome e email
- [ ] Verificar que tem links para "Meu Perfil" e "Configurações"
- [ ] Verificar que tem botão "Sair"

### 2. Sidebar
- [ ] Verificar que tem link para "Perfil"
- [ ] Clicar no link
- [ ] Verificar que vai para `/profile`

### 3. Responsividade
- [ ] Testar em mobile (DevTools > Toggle device toolbar)
- [ ] Verificar que o menu de perfil funciona
- [ ] Verificar que a página de login é responsiva
- [ ] Verificar que a página de perfil é responsiva

## 🐛 Testes de Erro

### 1. Erros de Login
- [ ] Tentar fazer login com email inexistente → Deve mostrar erro
- [ ] Tentar fazer login com senha errada → Deve mostrar erro
- [ ] Tentar criar conta com email já existente → Deve mostrar erro
- [ ] Tentar criar conta com senha < 6 caracteres → Deve mostrar erro

### 2. Erros de Rede
- [ ] Desligar o backend
- [ ] Tentar fazer login → Deve mostrar erro de conexão
- [ ] Tentar carregar leads → Deve mostrar erro
- [ ] Ligar o backend novamente
- [ ] Verificar que volta a funcionar

### 3. Erros de Permissão
- [ ] Fazer login
- [ ] Tentar acessar lead de outro usuário via URL direta
- [ ] Verificar que mostra erro 404 ou redireciona

## 📝 Checklist Final

- [ ] Todos os testes de autenticação passaram
- [ ] Todos os testes de perfil passaram
- [ ] Todos os testes de isolamento passaram
- [ ] Todos os testes de segurança passaram
- [ ] Todos os testes de estatísticas passaram
- [ ] Todos os testes de UI passaram
- [ ] Todos os testes de erro passaram

## 🎉 Sistema Pronto!

Se todos os testes passaram, o sistema de usuários está funcionando corretamente!

## 📞 Suporte

Se algum teste falhou, verifique:
1. Logs do backend
2. Console do navegador (DevTools)
3. Network tab (DevTools)
4. Supabase Dashboard (dados, RLS, storage)
5. Documentação em `USER_SYSTEM_README.md`
