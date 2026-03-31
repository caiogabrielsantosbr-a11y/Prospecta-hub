# ✅ Storage Bucket Criado com Sucesso!

## 🎉 O que foi feito automaticamente:

### Bucket `avatars` criado via SQL
```sql
✅ ID: avatars
✅ Nome: avatars
✅ Público: true
✅ Limite de tamanho: 2MB
✅ Tipos permitidos: JPEG, JPG, PNG, GIF, WEBP
✅ Status: ATIVO
```

## ⚠️ Falta apenas: Configurar Políticas RLS

As políticas RLS do storage precisam ser configuradas manualmente no dashboard do Supabase (restrição de permissões).

### Opção 1: Via Dashboard (Recomendado - 2 minutos)

1. Acesse https://app.supabase.com
2. Vá em **Storage** > **Policies**
3. Selecione o bucket **avatars**
4. Clique em **New Policy**

#### Política 1: Upload (INSERT)
- **Policy name**: Users can upload own avatar
- **Allowed operation**: INSERT
- **Target roles**: authenticated
- **USING expression**: 
  ```sql
  bucket_id = 'avatars' AND (storage.foldername(name))[1] = auth.uid()::text
  ```
- **WITH CHECK expression**:
  ```sql
  bucket_id = 'avatars' AND (storage.foldername(name))[1] = auth.uid()::text
  ```

#### Política 2: Visualização (SELECT)
- **Policy name**: Anyone can view avatars
- **Allowed operation**: SELECT
- **Target roles**: public
- **USING expression**:
  ```sql
  bucket_id = 'avatars'
  ```

#### Política 3: Atualização (UPDATE)
- **Policy name**: Users can update own avatar
- **Allowed operation**: UPDATE
- **Target roles**: authenticated
- **USING expression**:
  ```sql
  bucket_id = 'avatars' AND (storage.foldername(name))[1] = auth.uid()::text
  ```
- **WITH CHECK expression**:
  ```sql
  bucket_id = 'avatars' AND (storage.foldername(name))[1] = auth.uid()::text
  ```

#### Política 4: Exclusão (DELETE)
- **Policy name**: Users can delete own avatar
- **Allowed operation**: DELETE
- **Target roles**: authenticated
- **USING expression**:
  ```sql
  bucket_id = 'avatars' AND (storage.foldername(name))[1] = auth.uid()::text
  ```

### Opção 2: Via SQL Editor (Alternativa)

Se você tiver permissões de superusuário, pode executar no SQL Editor:

```sql
-- Habilitar RLS
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Política 1: Upload
CREATE POLICY "Users can upload own avatar" ON storage.objects
    FOR INSERT TO authenticated
    WITH CHECK (
        bucket_id = 'avatars' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

-- Política 2: Visualização
CREATE POLICY "Anyone can view avatars" ON storage.objects
    FOR SELECT TO public
    USING (bucket_id = 'avatars');

-- Política 3: Atualização
CREATE POLICY "Users can update own avatar" ON storage.objects
    FOR UPDATE TO authenticated
    USING (
        bucket_id = 'avatars' AND
        (storage.foldername(name))[1] = auth.uid()::text
    )
    WITH CHECK (
        bucket_id = 'avatars' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

-- Política 4: Exclusão
CREATE POLICY "Users can delete own avatar" ON storage.objects
    FOR DELETE TO authenticated
    USING (
        bucket_id = 'avatars' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );
```

### Opção 3: Usar Templates do Supabase (Mais Rápido)

1. Vá em **Storage** > **Policies**
2. Clique em **New Policy**
3. Escolha um template:
   - **Allow public read access** (para SELECT)
   - **Allow authenticated uploads** (para INSERT)
   - **Allow users to update their own files** (para UPDATE)
   - **Allow users to delete their own files** (para DELETE)

## 🧪 Como Testar

Após configurar as políticas:

1. Faça login na aplicação
2. Vá para **Perfil**
3. Clique em **Alterar Foto**
4. Selecione uma imagem
5. Verifique se o upload funciona
6. Verifique se a foto aparece no perfil

## ✅ Checklist Final

- [x] Bucket `avatars` criado
- [x] Bucket configurado como público
- [x] Limite de 2MB configurado
- [x] Tipos de imagem permitidos
- [ ] Políticas RLS configuradas (fazer manualmente)

## 🎯 Status Atual

**Bucket: 100% Pronto ✅**
**Políticas: Aguardando configuração manual (2 minutos)**

Depois de configurar as políticas, o sistema de upload de avatares estará 100% funcional!

## 📊 Verificar Bucket

Você pode verificar o bucket criado em:
- Dashboard: https://app.supabase.com → Storage → avatars
- SQL: `SELECT * FROM storage.buckets WHERE id = 'avatars';`

## 🔗 Links Úteis

- [Documentação Storage RLS](https://supabase.com/docs/guides/storage/security/access-control)
- [Exemplos de Políticas](https://supabase.com/docs/guides/storage/security/access-control#policy-examples)
