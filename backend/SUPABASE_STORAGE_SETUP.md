# Supabase Storage Setup Guide

## Problema
O erro "Failed to upload location file to storage" ocorre porque o bucket `location-files` não existe no Supabase Storage.

## Solução: Criar o Bucket Manualmente

Siga estes passos para criar o bucket no dashboard do Supabase:

### 1. Acesse o Dashboard do Supabase
- Vá para: https://supabase.com/dashboard
- Faça login na sua conta
- Selecione o projeto: `gyenypsxpidmsxabjhqg`

### 2. Navegue até Storage
- No menu lateral esquerdo, clique em **Storage**
- Você verá a lista de buckets existentes

### 3. Crie o Novo Bucket
- Clique no botão **"New bucket"** ou **"Create bucket"**
- Preencha os campos:
  - **Name**: `location-files`
  - **Public bucket**: ✅ **Marque esta opção** (importante para permitir downloads públicos)
  - **File size limit**: `10 MB` (10485760 bytes)
  - **Allowed MIME types**: `application/json` (opcional, mas recomendado)

### 4. Configurar Políticas (RLS)
Após criar o bucket, você precisa configurar as políticas de acesso:

#### Política 1: Public Read (Leitura Pública)
- Nome: `Public read access`
- Operação: `SELECT`
- Target roles: `public`, `anon`, `authenticated`
- Policy definition:
```sql
true
```

#### Política 2: Authenticated Write (Escrita Autenticada)
- Nome: `Authenticated write access`
- Operação: `INSERT`
- Target roles: `authenticated`, `service_role`
- Policy definition:
```sql
true
```

#### Política 3: Authenticated Delete (Exclusão Autenticada)
- Nome: `Authenticated delete access`
- Operação: `DELETE`
- Target roles: `authenticated`, `service_role`
- Policy definition:
```sql
true
```

### 5. Verificar a Configuração

Após criar o bucket, você pode verificar se está funcionando:

```bash
cd backend
python scripts/test_storage_upload.py
```

## Alternativa: Usar Service Role Key

Se você preferir criar o bucket via código, você precisa usar a `service_role` key (chave privada) ao invés da `anon` key.

### Onde encontrar a Service Role Key:
1. Vá para o dashboard do Supabase
2. Clique em **Settings** (Configurações)
3. Clique em **API**
4. Procure por **Project API keys**
5. Copie a chave **service_role** (⚠️ **NUNCA** exponha esta chave no frontend!)

### Adicionar ao .env:
```env
SUPABASE_SERVICE_ROLE_KEY=sua_service_role_key_aqui
```

### Executar o script de setup:
```bash
cd backend
python scripts/setup_storage_bucket_admin.py
```

## Estrutura do Bucket

Após a configuração, o bucket terá a seguinte estrutura:

```
location-files/
├── {uuid-1}.json
├── {uuid-2}.json
├── {uuid-3}.json
└── ...
```

Cada arquivo JSON contém:
```json
{
  "nome": "Nome do Conjunto",
  "descricao": "Descrição do conjunto",
  "locais": [
    "São Paulo, SP",
    "Rio de Janeiro, RJ",
    ...
  ]
}
```

## URLs de Acesso

Após o upload, os arquivos estarão disponíveis publicamente em:
```
https://gyenypsxpidmsxabjhqg.supabase.co/storage/v1/object/public/location-files/{uuid}.json
```

## Troubleshooting

### Erro: "Bucket not found"
- Verifique se o bucket foi criado com o nome exato: `location-files`
- Verifique se você está no projeto correto

### Erro: "Unauthorized" ou "403"
- Verifique se o bucket está marcado como **público**
- Verifique se as políticas RLS estão configuradas corretamente
- Verifique se você está usando a chave correta (anon key para leitura, service_role para admin)

### Erro: "File too large"
- Verifique se o arquivo JSON não excede 10MB
- Reduza o número de locais no conjunto se necessário

### Erro: "Invalid JSON"
- Verifique se o JSON está bem formatado
- Remova vírgulas extras (trailing commas)
- Use um validador JSON online para verificar

## Próximos Passos

Após configurar o bucket:

1. ✅ Tente criar um novo conjunto de locais na interface
2. ✅ Verifique se o arquivo foi criado no Storage
3. ✅ Teste o preview de locais
4. ✅ Teste a exclusão de conjuntos

## Suporte

Se você continuar tendo problemas:
1. Verifique os logs do backend: `backend/logs/`
2. Verifique o console do navegador (F12)
3. Verifique os logs do Supabase no dashboard
