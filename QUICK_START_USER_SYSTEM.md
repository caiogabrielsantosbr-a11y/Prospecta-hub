# 🚀 Guia Rápido - Sistema de Usuários

## ⚡ Início Rápido (5 minutos)

### 1. Configurar Supabase Storage (2 min)

1. Acesse https://app.supabase.com
2. Vá em **Storage** > **Create bucket**
3. Nome: `avatars`
4. Public: ✅ Ativado
5. Clique em **Create**

### 2. Configurar Backend (2 min)

```bash
# 1. Adicionar ao .env
echo "SUPABASE_JWT_SECRET=seu-jwt-secret-aqui" >> backend/.env

# 2. Instalar dependência
cd backend
pip install pyjwt

# 3. Reiniciar backend
# Ctrl+C e rodar novamente: python main.py
```

**Onde encontrar o JWT Secret:**
- Supabase Dashboard > Settings > API > JWT Secret

### 3. Testar (1 min)

1. Acesse http://localhost:5173/login
2. Crie uma conta
3. Faça login
4. Acesse seu perfil
5. Faça upload de uma foto

## ✅ Pronto!

O sistema básico está funcionando. Agora você pode:
- Criar múltiplos usuários
- Cada um terá seus próprios dados
- Todos compartilham os location_sets

## 📝 Próximos Passos

Para integração completa com os módulos existentes:

### Atualizar main.py

```python
# backend/main.py
from modules.leads.router import router as leads_router

app.include_router(leads_router)
```

### Testar Endpoints de Leads

```bash
# 1. Fazer login e obter token
# (use o DevTools > Application > Local Storage)

# 2. Testar endpoint
curl -X GET "http://localhost:8000/api/leads" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

## 🔧 Integração com Módulos Existentes

Siga o guia detalhado em `USER_SYSTEM_INTEGRATION.md` para:
- Atualizar módulo GMap
- Atualizar módulo Facebook Ads
- Atualizar módulo Email Dispatch

## 📚 Documentação Completa

- `USER_SYSTEM_README.md` - Documentação completa
- `USER_SYSTEM_INTEGRATION.md` - Guia de integração
- `TEST_USER_SYSTEM.md` - Checklist de testes
- `IMPLEMENTATION_SUMMARY.md` - Resumo da implementação

## 🐛 Problemas Comuns

### Erro: "Missing authorization header"
```bash
# Verifique se o token está sendo enviado
# DevTools > Network > Headers > Authorization
```

### Erro: "Invalid token"
```bash
# Verifique se SUPABASE_JWT_SECRET está correto
# Deve ser o mesmo do Supabase Dashboard
```

### Erro ao fazer upload de foto
```bash
# Verifique se o bucket 'avatars' foi criado
# Verifique se é público
```

## 💡 Dica

Use dois navegadores diferentes (ou modo anônimo) para testar com dois usuários simultaneamente e verificar o isolamento de dados!

## 🎉 Tudo Funcionando?

Execute o checklist completo em `TEST_USER_SYSTEM.md` para garantir que tudo está perfeito!
