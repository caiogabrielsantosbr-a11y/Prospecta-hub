# Solução: "Failed to upload location file to storage"

## Problema
O erro ocorre porque o bucket `location-files` não existe no Supabase Storage.

## Solução Rápida (5 minutos)

### Passo 1: Acesse o Dashboard do Supabase
1. Vá para: https://supabase.com/dashboard
2. Faça login
3. Selecione seu projeto

### Passo 2: Crie o Bucket
1. No menu lateral, clique em **Storage**
2. Clique em **"New bucket"**
3. Preencha:
   - **Name**: `location-files`
   - **Public bucket**: ✅ **MARQUE ESTA OPÇÃO**
   - **File size limit**: `10 MB`
4. Clique em **"Create bucket"**

### Passo 3: Configure as Políticas (RLS)
Após criar o bucket, você precisa adicionar políticas de acesso:

1. Clique no bucket `location-files` que você acabou de criar
2. Vá para a aba **"Policies"**
3. Clique em **"New Policy"**

#### Política 1: Leitura Pública
- **Policy name**: `Public read access`
- **Allowed operation**: `SELECT`
- **Target roles**: Selecione `public`, `anon`, `authenticated`
- **USING expression**: Digite `true`
- Clique em **"Review"** e depois **"Save policy"**

#### Política 2: Escrita Autenticada
- **Policy name**: `Authenticated write access`
- **Allowed operation**: `INSERT`
- **Target roles**: Selecione `authenticated`, `service_role`
- **USING expression**: Digite `true`
- Clique em **"Review"** e depois **"Save policy"**

#### Política 3: Exclusão Autenticada
- **Policy name**: `Authenticated delete access`
- **Allowed operation**: `DELETE`
- **Target roles**: Selecione `authenticated`, `service_role`
- **USING expression**: Digite `true`
- Clique em **"Review"** e depois **"Save policy"**

### Passo 4: Teste a Configuração
Execute o script de teste:

```bash
cd backend
python scripts/test_storage_upload.py
```

Se você ver "✅ All tests passed!", está tudo funcionando!

### Passo 5: Tente Criar o Conjunto Novamente
Agora você pode voltar para a interface e tentar criar o conjunto de locais novamente com o JSON:

```json
[
  "Taubaté - SP",
  "Suzano - SP",
  "Limeira - SP",
  "Guarujá - SP",
  "Sumaré - SP",
  "Cotia - SP"
]
```

## Verificação Visual

Após criar um conjunto com sucesso, você pode verificar no Supabase:
1. Vá para **Storage** > **location-files**
2. Você verá arquivos com nomes como `a1b2c3d4-e5f6-7890-abcd-ef1234567890.json`
3. Clique em um arquivo para ver seu conteúdo

## Troubleshooting

### Ainda recebendo erro 403?
- Verifique se o bucket está marcado como **público**
- Verifique se as 3 políticas foram criadas corretamente
- Tente recarregar a página do dashboard

### Erro "Bucket not found"?
- Verifique se o nome do bucket é exatamente `location-files` (sem espaços, tudo minúsculo)
- Verifique se você está no projeto correto

### Precisa de ajuda?
Consulte o guia completo em: `backend/SUPABASE_STORAGE_SETUP.md`
