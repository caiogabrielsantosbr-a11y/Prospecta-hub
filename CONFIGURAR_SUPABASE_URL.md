# 🔧 Configurar URL de Redirecionamento no Supabase

## ❌ Problema Atual

O Supabase está redirecionando para `http://localhost:3000` mas sua aplicação está em:
- **Produção**: https://prospecta-hub.vercel.app
- **Desenvolvimento**: http://localhost:5173

## ✅ Solução (2 minutos)

### Passo 1: Acessar Configurações do Supabase

1. Acesse https://app.supabase.com
2. Selecione seu projeto: **gyenypsxpidmsxabjhqg**
3. Vá em **Authentication** (menu lateral)
4. Clique em **URL Configuration**

### Passo 2: Configurar URLs

#### Site URL
```
https://prospecta-hub.vercel.app
```

#### Redirect URLs (adicione ambas)
```
https://prospecta-hub.vercel.app/**
http://localhost:5173/**
```

**Importante**: Adicione as duas URLs separadas por vírgula ou uma por linha.

### Passo 3: Salvar

Clique em **Save** no final da página.

## 🧪 Testar

1. Acesse https://prospecta-hub.vercel.app/login
2. Crie uma nova conta ou faça login
3. Verifique seu email
4. Clique no link de confirmação
5. Deve redirecionar para https://prospecta-hub.vercel.app/ ✅

## 📝 O que foi atualizado no código

### 1. AuthContext.jsx
- ✅ Adicionado `emailRedirectTo` dinâmico
- ✅ Melhor tratamento de eventos de auth
- ✅ Mensagens de toast mais claras

### 2. AuthCallbackPage.jsx (NOVO)
- ✅ Página para lidar com confirmação de email
- ✅ Processa token do URL
- ✅ Redireciona para home após confirmação

### 3. App.jsx
- ✅ Rota `/auth/callback` adicionada

## 🔄 Fluxo de Confirmação de Email

```
1. Usuário cria conta
   ↓
2. Supabase envia email
   ↓
3. Usuário clica no link do email
   ↓
4. Redireciona para: https://prospecta-hub.vercel.app/#access_token=...
   ↓
5. AuthCallbackPage processa o token
   ↓
6. Usuário é autenticado
   ↓
7. Redireciona para home (/)
```

## 🚀 Fazer Deploy das Mudanças

```bash
git add .
git commit -m "fix: Configurar redirect URL para Vercel"
git push origin main
```

O Vercel vai fazer deploy automaticamente.

## 🐛 Troubleshooting

### Email não chega
- Verifique spam/lixo eletrônico
- Aguarde alguns minutos
- Tente reenviar email de confirmação

### Link quebrado
- Verifique se configurou as URLs no Supabase
- Limpe cache do navegador
- Tente em modo anônimo

### Ainda redireciona para localhost:3000
- Aguarde 1-2 minutos após salvar no Supabase
- Limpe cache do navegador
- Faça logout e login novamente

## 📖 Documentação Supabase

- [URL Configuration](https://supabase.com/docs/guides/auth/redirect-urls)
- [Email Templates](https://supabase.com/docs/guides/auth/auth-email-templates)

---

**Depois de configurar, o sistema estará 100% funcional em produção!** 🎉
