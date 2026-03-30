# Checklist de Deploy - Prospecta HUB

## ✅ Preparação Concluída

- [x] Código enviado para GitHub
- [x] Diretório `frontend` selecionado no Vercel
- [x] Arquivo `vercel.json` criado para roteamento SPA
- [x] Documentação de deploy criada

## 📋 Próximos Passos no Vercel

### 1. Configurações de Build (já preenchidas automaticamente)
```
Root Directory: frontend
Build Command: npm run build
Output Directory: dist
Install Command: npm install
```

### 2. Variáveis de Ambiente (IMPORTANTE!)

Antes de fazer o deploy, adicione estas variáveis em "Environment Variables":

| Nome | Valor | Onde Obter |
|------|-------|------------|
| `VITE_SUPABASE_URL` | URL do projeto Supabase | Supabase > Settings > API > Project URL |
| `VITE_SUPABASE_KEY` | Chave anônima do Supabase | Supabase > Settings > API > anon/public key |

### 3. Deploy
- Clique em "Deploy"
- Aguarde o build (leva ~2-3 minutos)
- Anote a URL gerada (ex: `prospecta-hub.vercel.app`)

## 🔧 Configuração Pós-Deploy

### Atualizar URL do Frontend no Supabase

Após o deploy, você precisa atualizar a URL do frontend na tabela `app_settings`:

```sql
-- Execute no SQL Editor do Supabase
UPDATE app_settings 
SET frontend_url = 'https://sua-url.vercel.app'
WHERE id = 1;
```

### Configurar CORS no Backend (se necessário)

Se houver erros de CORS, adicione a URL do Vercel nas origens permitidas no backend:

```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://sua-url.vercel.app"  # Adicione esta linha
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🧪 Testes Pós-Deploy

Acesse a URL do Vercel e teste:

- [ ] Página inicial carrega
- [ ] Menu de navegação funciona
- [ ] Página de Google Maps abre
- [ ] Dropdown de conjuntos de locais carrega
- [ ] Modal de gerenciar conjuntos abre
- [ ] Console do navegador não mostra erros críticos

## 📱 URLs Importantes

- **Frontend (Vercel)**: `https://_____.vercel.app` (será gerado)
- **Backend (ngrok)**: Configurado no Supabase
- **Supabase Dashboard**: `https://supabase.com/dashboard`

## 🚨 Troubleshooting Comum

### Página em branco após deploy
- Verifique as variáveis de ambiente no Vercel
- Abra o console do navegador para ver erros
- Verifique os logs de build no Vercel

### Erro 404 ao navegar entre páginas
- Confirme que `vercel.json` existe em `frontend/`
- Faça um novo deploy se necessário

### Erro ao conectar com backend
- Verifique se o backend está rodando (ngrok ativo)
- Confirme que a URL do backend está atualizada no Supabase
- Verifique CORS no backend

### Conjuntos de locais não carregam
- Verifique as credenciais do Supabase
- Confirme que as tabelas existem no banco
- Verifique as políticas RLS no Supabase

## 📚 Documentação Adicional

- `frontend/VERCEL_DEPLOY.md` - Guia detalhado de deploy
- `frontend/.env.example` - Exemplo de variáveis de ambiente
- `backend/SUPABASE_CLIENT_README.md` - Documentação do cliente Supabase

## 🎉 Deploy Completo!

Quando tudo estiver funcionando:
1. Compartilhe a URL do Vercel com sua equipe
2. Atualize o README principal com a URL de produção
3. Configure domínio customizado no Vercel (opcional)
