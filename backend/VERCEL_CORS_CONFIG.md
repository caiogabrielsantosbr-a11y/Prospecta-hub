# Configuração CORS para Vercel

## ⚠️ AÇÃO NECESSÁRIA

Para que o frontend no Vercel consiga se conectar ao backend, você precisa adicionar a URL do Vercel no arquivo `backend/.env`.

## Configuração Atual Necessária

Edite o arquivo `backend/.env` e atualize a linha `CORS_ORIGINS` para incluir a URL do Vercel:

```env
CORS_ORIGINS=http://localhost:5173,https://unsought-deadra-lichenlike.ngrok-free.dev,https://prospecta-hub.vercel.app
```

## Como Aplicar

1. Abra o arquivo `backend/.env`
2. Localize a linha que começa com `CORS_ORIGINS=`
3. Adicione `,https://prospecta-hub.vercel.app` no final
4. Salve o arquivo
5. **Reinicie o backend** (Ctrl+C e depois `python main.py`)

## Verificação

Após reiniciar o backend, você deve ver no console:

```
[CORS] Configured origins: ['http://localhost:5173', 'https://unsought-deadra-lichenlike.ngrok-free.dev', 'https://prospecta-hub.vercel.app']
```

## Teste

1. Acesse https://prospecta-hub.vercel.app
2. Vá para "Configurações"
3. Cole a URL do ngrok: `https://unsought-deadra-lichenlike.ngrok-free.dev`
4. Clique em "Salvar e Testar"
5. O status deve mudar para "Conectado" ✅

## URLs Configuradas

- **Local**: http://localhost:5173
- **Ngrok**: https://unsought-deadra-lichenlike.ngrok-free.dev
- **Vercel**: https://prospecta-hub.vercel.app

---

**Nota**: O arquivo `.env` não é versionado no Git por questões de segurança, então você precisa fazer essa alteração manualmente no seu ambiente local.
