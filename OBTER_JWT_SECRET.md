# 🔑 Como Obter o JWT Secret do Supabase

## Por que preciso disso?
O backend FastAPI precisa do JWT Secret para validar os tokens de autenticação enviados pelo frontend. Sem isso, todas as requisições autenticadas falharão.

## Passo a Passo

### 1. Acesse o Dashboard do Supabase
Abra: https://app.supabase.com/project/gyenypsxpidmsxabjhqg/settings/api

### 2. Localize o JWT Secret
Na página de configurações da API, você verá várias chaves:
- **Project URL** ✅ (já temos)
- **anon public** ✅ (já temos)
- **service_role** (não precisamos)
- **JWT Secret** ⬅️ **É ESTE QUE PRECISAMOS!**

### 3. Copie o JWT Secret
Clique no ícone de "copiar" ao lado do JWT Secret.

**IMPORTANTE:** O JWT Secret é diferente das API keys! Ele é uma string longa usada para assinar tokens.

### 4. Cole no arquivo .env
Abra o arquivo `backend/.env` e substitua a linha:
```env
SUPABASE_JWT_SECRET=your-jwt-secret-here
```

Por:
```env
SUPABASE_JWT_SECRET=o-valor-que-voce-copiou
```

### 5. Reinicie o backend
No terminal onde o uvicorn está rodando:
1. Pressione `Ctrl+C` para parar
2. Execute novamente:
   ```bash
   cd backend
   uvicorn main:app --host 0.0.0.0 --port 8001
   ```

## Verificar se funcionou
Após reiniciar, teste um endpoint autenticado do frontend. Se não houver erro de autenticação, está funcionando!

## Segurança
⚠️ **NUNCA** compartilhe o JWT Secret publicamente ou faça commit dele no Git!
O arquivo `.env` já está no `.gitignore` para proteger suas credenciais.
