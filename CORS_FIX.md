# Como Corrigir a Conexão do Frontend (Vercel) com o Backend (ngrok)

## Problema
O frontend em produção no Vercel não consegue se conectar ao backend porque o backend está bloqueando requisições CORS de origens não autorizadas.

## Solução

### Passo 1: Obter a URL do Vercel
Após o deploy no Vercel, você recebeu uma URL como:
- `https://prospecta-hub.vercel.app` (exemplo)
- ou `https://seu-projeto-xyz.vercel.app`

### Passo 2: Adicionar a URL no Backend

Edite o arquivo `backend/.env` e adicione a URL do Vercel na variável `CORS_ORIGINS`:

```env
CORS_ORIGINS=http://localhost:5173,https://unsought-deadra-lichenlike.ngrok-free.dev,https://sua-url.vercel.app
```

**Exemplo completo:**
```env
CORS_ORIGINS=http://localhost:5173,https://unsought-deadra-lichenlike.ngrok-free.dev,https://prospecta-hub.vercel.app
```

### Passo 3: Reiniciar o Backend

Depois de editar o `.env`, você precisa:

1. **Parar o backend** (Ctrl+C no terminal onde está rodando)
2. **Reiniciar o backend**:
   ```bash
   cd backend
   python main.py
   ```
3. **Verificar se o ngrok ainda está ativo** - se não estiver, reinicie:
   ```bash
   ngrok http 8000
   ```

### Passo 4: Testar a Conexão

1. Acesse seu site no Vercel
2. Vá para a página de "Configurações"
3. Cole a URL do ngrok: `https://unsought-deadra-lichenlike.ngrok-free.dev`
4. Clique em "Salvar e Testar"
5. O status deve mudar para "Conectado" (verde)

## Verificação

Se ainda não funcionar, abra o Console do navegador (F12) e verifique:

1. **Erro de CORS**: Se aparecer erro de CORS, significa que a URL do Vercel não foi adicionada corretamente no backend
2. **Erro de rede**: Se aparecer erro de rede, verifique se o backend e ngrok estão rodando
3. **Erro 502/504**: O ngrok pode ter expirado - reinicie o ngrok

## Dica: Manter o Backend Rodando

Para evitar ter que reiniciar o ngrok toda hora (a URL muda), considere:

1. **ngrok com domínio fixo** (plano pago)
2. **Cloudflare Tunnel** (gratuito, domínio fixo)
3. **localtunnel com subdomain** (gratuito, mas menos estável)

## Resumo dos Arquivos Modificados

- ✅ `frontend/src/store/useConfigStore.js` - Adicionado header `ngrok-skip-browser-warning`
- ⚠️ `backend/.env` - **VOCÊ PRECISA ADICIONAR** a URL do Vercel aqui

## Próximos Passos

1. Copie a URL do Vercel
2. Adicione no `backend/.env` na variável `CORS_ORIGINS`
3. Reinicie o backend
4. Teste a conexão no site em produção
