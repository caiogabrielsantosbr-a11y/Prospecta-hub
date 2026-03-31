# 🔧 Resolver Erro de Upload de Avatar

## 🎯 Problema

"Erro ao fazer upload da foto" - Isso acontece porque as políticas RLS do storage não foram configuradas.

## ✅ Solução (3 opções)

### Opção 1: Via SQL Editor (Mais Rápido - 1 minuto)

1. Acesse: https://app.supabase.com/project/gyenypsxpidmsxabjhqg/sql/new
2. Cole o conteúdo do arquivo `CONFIGURAR_STORAGE_POLICIES.sql`
3. Clique em **Run** (ou pressione Ctrl+Enter)
4. Aguarde a confirmação de sucesso
5. Teste o upload novamente

### Opção 2: Via Dashboard (Mais Visual - 3 minutos)

1. Acesse: https://app.supabase.com/project/gyenypsxpidmsxabjhqg/storage/policies
2. Selecione o bucket **avatars**
3. Clique em **New Policy**

#### Política 1: Upload (INSERT)
- **Policy name**: `Users can upload own avatar`
- **Allowed operation**: INSERT
- **Target roles**: authenticated
- **Policy definition**:
  ```sql
  (bucket_id = 'avatars'::text) AND ((storage.foldername(name))[1] = (auth.uid())::text)
  ```

#### Política 2: Visualização (SELECT)
- **Policy name**: `Anyone can view avatars`
- **Allowed operation**: SELECT
- **Target roles**: public
- **Policy definition**:
  ```sql
  bucket_id = 'avatars'::text
  ```

#### Política 3: Atualização (UPDATE)
- **Policy name**: `Users can update own avatar`
- **Allowed operation**: UPDATE
- **Target roles**: authenticated
- **Policy definition**:
  ```sql
  (bucket_id = 'avatars'::text) AND ((storage.foldername(name))[1] = (auth.uid())::text)
  ```

#### Política 4: Exclusão (DELETE)
- **Policy name**: `Users can delete own avatar`
- **Allowed operation**: DELETE
- **Target roles**: authenticated
- **Policy definition**:
  ```sql
  (bucket_id = 'avatars'::text) AND ((storage.foldername(name))[1] = (auth.uid())::text)
  ```

### Opção 3: Usar Templates (Mais Fácil - 2 minutos)

1. Acesse: https://app.supabase.com/project/gyenypsxpidmsxabjhqg/storage/policies
2. Selecione o bucket **avatars**
3. Clique em **New Policy**
4. Escolha um template:
   - **"Allow public read access"** para SELECT
   - **"Allow authenticated uploads"** para INSERT
   - **"Allow users to update their own files"** para UPDATE
   - **"Allow users to delete their own files"** para DELETE

## 🧪 Testar

Após configurar as políticas:

1. Acesse https://prospecta-hub.vercel.app/profile
2. Clique em **Alterar Foto**
3. Selecione uma imagem (JPEG, PNG, GIF, WEBP)
4. Máximo 2MB
5. Deve fazer upload com sucesso ✅

## 🔍 Verificar se Funcionou

### No Console do Navegador (F12)

Você deve ver:
```
Uploading avatar: cc4fe1bc-b03f-4970-bfd4-0f022dbd8ed4/1234567890.jpg
Upload successful: { path: "...", id: "...", fullPath: "..." }
Public URL: https://gyenypsxpidmsxabjhqg.supabase.co/storage/v1/object/public/avatars/...
```

### No Supabase Dashboard

1. Vá em **Storage** > **avatars**
2. Deve ver sua foto na pasta com seu user_id

## 🐛 Troubleshooting

### Erro: "new row violates row-level security policy"
- **Causa**: Políticas RLS não configuradas
- **Solução**: Execute o SQL ou configure via dashboard

### Erro: "Bucket not found"
- **Causa**: Bucket 'avatars' não existe
- **Solução**: Execute:
  ```sql
  SELECT * FROM storage.buckets WHERE id = 'avatars';
  ```
  Se não retornar nada, o bucket não foi criado.

### Erro: "File size too large"
- **Causa**: Imagem maior que 2MB
- **Solução**: Comprima a imagem ou escolha outra

### Erro: "Invalid file type"
- **Causa**: Arquivo não é uma imagem
- **Solução**: Selecione JPEG, PNG, GIF ou WEBP

## 📊 Estrutura de Pastas

O upload organiza as fotos por usuário:
```
avatars/
├── cc4fe1bc-b03f-4970-bfd4-0f022dbd8ed4/
│   ├── 1234567890.jpg
│   └── 1234567891.jpg
└── outro-user-id/
    └── foto.png
```

## 🔐 Segurança

As políticas RLS garantem que:
- ✅ Usuários só podem fazer upload em sua própria pasta
- ✅ Todos podem visualizar avatares (bucket público)
- ✅ Usuários só podem atualizar/deletar suas próprias fotos
- ❌ Usuários não podem acessar fotos de outros usuários (exceto visualização)

## 📝 Melhorias no Código

O código foi atualizado para:
- ✅ Validar tipo de arquivo
- ✅ Validar tamanho (2MB)
- ✅ Organizar por pasta de usuário
- ✅ Usar `upsert: true` para substituir fotos antigas
- ✅ Logs detalhados no console
- ✅ Mensagens de erro específicas

## 🚀 Próximos Passos

Depois de configurar as políticas:
1. Teste o upload
2. Verifique se a foto aparece no perfil
3. Teste com outro usuário para confirmar isolamento
4. Faça commit das mudanças:
   ```bash
   git add .
   git commit -m "fix: Melhorar upload de avatar com validações"
   git push origin main
   ```

---

**Depois de configurar as políticas, o upload funcionará perfeitamente!** 🎉
