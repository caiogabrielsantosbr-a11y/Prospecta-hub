# Configuração do Storage para Avatares

Para habilitar o upload de fotos de perfil, você precisa criar um bucket de storage no Supabase:

## Passos:

1. Acesse o painel do Supabase: https://app.supabase.com
2. Vá para **Storage** no menu lateral
3. Clique em **Create a new bucket**
4. Configure o bucket:
   - **Name**: `avatars`
   - **Public bucket**: ✅ Ativado (para que as fotos sejam acessíveis publicamente)
5. Clique em **Create bucket**

## Políticas de Segurança (RLS)

Após criar o bucket, configure as seguintes políticas:

### 1. Upload de Avatar (INSERT)
```sql
CREATE POLICY "Users can upload own avatar" ON storage.objects
    FOR INSERT
    WITH CHECK (
        bucket_id = 'avatars' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );
```

### 2. Visualização de Avatares (SELECT)
```sql
CREATE POLICY "Anyone can view avatars" ON storage.objects
    FOR SELECT
    USING (bucket_id = 'avatars');
```

### 3. Atualização de Avatar (UPDATE)
```sql
CREATE POLICY "Users can update own avatar" ON storage.objects
    FOR UPDATE
    USING (
        bucket_id = 'avatars' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );
```

### 4. Exclusão de Avatar (DELETE)
```sql
CREATE POLICY "Users can delete own avatar" ON storage.objects
    FOR DELETE
    USING (
        bucket_id = 'avatars' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );
```

## Alternativa: Criar via Dashboard

Você também pode criar essas políticas diretamente no dashboard do Supabase:

1. Vá para **Storage** > **Policies**
2. Selecione o bucket `avatars`
3. Clique em **New Policy**
4. Configure cada política conforme descrito acima

## Verificação

Após configurar, teste o upload de uma foto de perfil na página de perfil do usuário.
