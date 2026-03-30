# Deploy Frontend no Vercel

## Configurações do Projeto

### Root Directory
```
frontend
```

### Build Settings
**IMPORTANTE**: Os comandos de build estão configurados no arquivo `vercel.json` e não podem ser editados na interface do Vercel quando um Framework Preset está selecionado. Isso é normal e esperado.

O arquivo `vercel.json` já contém:
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "installCommand": "npm install"
}
```

### Framework Preset
Vite (pode deixar selecionado - o vercel.json vai fazer o override dos comandos)

## Variáveis de Ambiente

Configure as seguintes variáveis de ambiente no painel do Vercel:

### Obrigatórias
- `VITE_SUPABASE_URL`: URL do seu projeto Supabase
- `VITE_SUPABASE_KEY`: Chave anônima (anon key) do Supabase

### Como obter as credenciais do Supabase
1. Acesse [supabase.com](https://supabase.com)
2. Vá para o seu projeto
3. Clique em "Settings" > "API"
4. Copie:
   - **Project URL** → `VITE_SUPABASE_URL`
   - **anon/public key** → `VITE_SUPABASE_KEY`

## Passos para Deploy

1. **Conectar Repositório**
   - Importe o projeto do GitHub no Vercel
   - Selecione o repositório `Plataforma-Prospect`

2. **Configurar Root Directory**
   - Selecione `frontend` como Root Directory

3. **Adicionar Variáveis de Ambiente**
   - Vá para "Environment Variables"
   - Adicione `VITE_SUPABASE_URL` e `VITE_SUPABASE_KEY`

4. **Deploy**
   - Clique em "Deploy"
   - Aguarde o build completar

## Verificações Pós-Deploy

Após o deploy, verifique:

- [ ] A página inicial carrega corretamente
- [ ] O menu de navegação funciona
- [ ] A conexão com Supabase está funcionando (verifique no console do navegador)
- [ ] As rotas do React Router funcionam (navegação entre páginas)

## Troubleshooting

### Erro 404 ao navegar
- Verifique se o arquivo `vercel.json` existe no diretório `frontend`
- Deve conter a configuração de rewrite para SPA

### Erro de conexão com backend
- O frontend se conecta ao backend via URL configurada no Supabase
- Certifique-se de que a URL do backend (ngrok) está atualizada nas configurações do app no Supabase

### Build falha
- Verifique se todas as dependências estão no `package.json`
- Confirme que o comando `npm run build` funciona localmente

## Notas Importantes

- O frontend é uma SPA (Single Page Application) que se comunica com o backend via API
- O backend deve estar rodando separadamente (não é deployado no Vercel)
- A URL do backend é configurada dinamicamente via Supabase (tabela `app_settings`)
