# Tunnel Setup Guide

Este guia explica como expor seu backend FastAPI local para a internet usando serviços de túnel reverso, permitindo que o frontend hospedado no Vercel se conecte ao seu ambiente de desenvolvimento local.

## Índice

- [Visão Geral](#visão-geral)
- [Opções de Túnel](#opções-de-túnel)
  - [ngrok (Recomendado)](#ngrok-recomendado)
  - [localtunnel](#localtunnel)
  - [Cloudflare Tunnel](#cloudflare-tunnel)
- [Configuração do Backend](#configuração-do-backend)
- [Troubleshooting](#troubleshooting)
- [Checklist de Deployment](#checklist-de-deployment)

## Visão Geral

Para conectar o frontend em produção (Vercel) ao seu backend local, você precisa:

1. **Expor o backend local** através de um túnel reverso
2. **Configurar CORS** no backend para aceitar requisições do Vercel
3. **Configurar a URL do túnel** no painel administrativo do frontend

```
┌─────────────────┐         HTTPS          ┌──────────────┐
│  Vercel         │ ──────────────────────> │  Túnel       │
│  (Frontend)     │                         │  (ngrok/etc) │
└─────────────────┘                         └──────────────┘
                                                    │
                                                    │ HTTP
                                                    ▼
                                            ┌──────────────┐
                                            │  Backend     │
                                            │  localhost   │
                                            │  :8000       │
                                            └──────────────┘
```

## Opções de Túnel

### ngrok (Recomendado)

**Vantagens:**
- Interface web para monitoramento de requisições
- URLs estáveis (com conta paga)
- Suporte a WebSocket
- Fácil de usar

**Instalação:**

```bash
# Windows (via Chocolatey)
choco install ngrok

# macOS (via Homebrew)
brew install ngrok/ngrok/ngrok

# Linux (via snap)
snap install ngrok

# Ou baixe diretamente de https://ngrok.com/download
```

**Configuração:**

1. Crie uma conta gratuita em [ngrok.com](https://ngrok.com)
2. Obtenha seu token de autenticação
3. Configure o token:

```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

**Uso:**

```bash
# Inicie o backend primeiro
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Em outro terminal, inicie o ngrok
ngrok http 8000
```

**Saída esperada:**

```
ngrok                                                                    

Session Status                online
Account                       seu-email@example.com
Version                       3.x.x
Region                        United States (us)
Latency                       45ms
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123def456.ngrok-free.app -> http://localhost:8000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

**URL para configurar no frontend:**
```
https://abc123def456.ngrok-free.app
```

**Interface Web:**
- Acesse `http://127.0.0.1:4040` para ver requisições em tempo real
- Útil para debugging de CORS e WebSocket

---

### localtunnel

**Vantagens:**
- Não requer conta ou autenticação
- Instalação via npm
- Open source

**Desvantagens:**
- URLs mudam a cada execução
- Menos estável que ngrok
- Pode ter problemas com WebSocket

**Instalação:**

```bash
npm install -g localtunnel
```

**Uso:**

```bash
# Inicie o backend primeiro
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Em outro terminal, inicie o localtunnel
lt --port 8000
```

**Saída esperada:**

```
your url is: https://funny-cat-123.loca.lt
```

**URL para configurar no frontend:**
```
https://funny-cat-123.loca.lt
```

**Nota:** Na primeira vez que acessar a URL, você verá uma página de aviso. Clique em "Continue" para prosseguir.

**Subdomínio customizado (opcional):**

```bash
lt --port 8000 --subdomain meu-backend
# URL: https://meu-backend.loca.lt
```

---

### Cloudflare Tunnel

**Vantagens:**
- Infraestrutura robusta da Cloudflare
- URLs permanentes
- Suporte a múltiplos serviços
- Segurança adicional

**Desvantagens:**
- Configuração mais complexa
- Requer conta Cloudflare

**Instalação:**

```bash
# Windows (via Chocolatey)
choco install cloudflared

# macOS (via Homebrew)
brew install cloudflare/cloudflare/cloudflared

# Linux
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

**Configuração:**

1. Autentique-se:

```bash
cloudflared tunnel login
```

2. Crie um túnel:

```bash
cloudflared tunnel create meu-backend
```

3. Configure o túnel (crie arquivo `config.yml`):

```yaml
tunnel: <TUNNEL-ID>
credentials-file: /path/to/.cloudflared/<TUNNEL-ID>.json

ingress:
  - hostname: meu-backend.example.com
    service: http://localhost:8000
  - service: http_status:404
```

4. Configure DNS:

```bash
cloudflared tunnel route dns meu-backend meu-backend.example.com
```

**Uso:**

```bash
# Inicie o backend primeiro
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Em outro terminal, inicie o túnel
cloudflared tunnel run meu-backend
```

**URL para configurar no frontend:**
```
https://meu-backend.example.com
```

**Modo rápido (sem configuração permanente):**

```bash
cloudflared tunnel --url http://localhost:8000
```

Isso gera uma URL temporária como `https://random-words.trycloudflare.com`

---

## Configuração do Backend

### 1. Configurar CORS_ORIGINS

Edite o arquivo `backend/.env`:

```bash
# Adicione a URL do Vercel às origens permitidas
CORS_ORIGINS=http://localhost:5173,https://seu-app.vercel.app,https://seu-app-*.vercel.app
```

**Formato:**
- Múltiplas origens separadas por vírgula
- Sem espaços entre as URLs
- Inclua tanto localhost (desenvolvimento) quanto Vercel (produção)
- Use wildcard `*` para aceitar todos os preview deployments do Vercel

**Exemplo completo:**

```bash
# .env
CORS_ORIGINS=http://localhost:5173,https://prospecta-frontend.vercel.app,https://prospecta-frontend-*.vercel.app
```

### 2. Verificar configuração no código

O arquivo `backend/main.py` deve conter:

```python
import os

# CORS Configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
cors_origins = [origin.strip() for origin in cors_origins]

print(f"[CORS] Configured origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.io CORS
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=cors_origins,  # Mesma lista do FastAPI
    logger=False,
    engineio_logger=False
)
```

### 3. Reiniciar o backend

Após modificar o `.env`, reinicie o servidor:

```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Verifique nos logs se as origens foram carregadas corretamente:

```
[CORS] Configured origins: ['http://localhost:5173', 'https://seu-app.vercel.app', 'https://seu-app-*.vercel.app']
```

---

## Troubleshooting

### Problema: "Backend não respondeu - verifique se o túnel está ativo"

**Causas possíveis:**
- Túnel não está rodando
- Backend não está rodando
- URL configurada incorretamente

**Soluções:**

1. Verifique se o backend está rodando:
```bash
curl http://localhost:8000/api/health
# Deve retornar: {"status":"ok"}
```

2. Verifique se o túnel está ativo:
```bash
# Para ngrok: acesse http://127.0.0.1:4040
# Para localtunnel: verifique se o processo está rodando
# Para Cloudflare: execute cloudflared tunnel info
```

3. Teste a URL do túnel diretamente:
```bash
curl https://sua-url-do-tunel.ngrok-free.app/api/health
```

---

### Problema: "Erro de CORS - adicione a URL do Vercel no CORS_ORIGINS"

**Causas possíveis:**
- URL do Vercel não está em CORS_ORIGINS
- Formato incorreto no .env
- Backend não foi reiniciado após alterar .env

**Soluções:**

1. Verifique o arquivo `backend/.env`:
```bash
cat backend/.env | grep CORS_ORIGINS
```

2. Certifique-se de incluir a URL exata do Vercel:
```bash
# Obtenha a URL do Vercel no dashboard ou no deploy log
CORS_ORIGINS=http://localhost:5173,https://seu-app-git-main-seu-usuario.vercel.app
```

3. Reinicie o backend:
```bash
# Ctrl+C para parar
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4. Verifique os logs do backend para confirmar:
```
[CORS] Configured origins: ['http://localhost:5173', 'https://seu-app-git-main-seu-usuario.vercel.app']
```

---

### Problema: WebSocket não conecta

**Causas possíveis:**
- Túnel não suporta WebSocket
- CORS do Socket.io não configurado
- Firewall bloqueando conexões

**Soluções:**

1. Verifique se o túnel suporta WebSocket:
   - **ngrok**: ✅ Suporta
   - **localtunnel**: ⚠️ Suporte limitado
   - **Cloudflare**: ✅ Suporta

2. Verifique configuração do Socket.io no backend:
```python
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=cors_origins,  # Deve ser a mesma lista do CORS
    logger=True,  # Ative para debug
    engineio_logger=True
)
```

3. Teste a conexão WebSocket:
```javascript
// No console do navegador
const socket = io('https://sua-url-do-tunel.ngrok-free.app')
socket.on('connect', () => console.log('Connected!'))
socket.on('connect_error', (err) => console.error('Error:', err))
```

---

### Problema: ngrok mostra "ERR_NGROK_108"

**Causa:**
- Limite de conexões da conta gratuita atingido

**Solução:**
- Aguarde alguns minutos
- Ou faça upgrade para conta paga
- Ou use localtunnel/Cloudflare como alternativa

---

### Problema: localtunnel mostra página de aviso

**Causa:**
- Comportamento padrão do localtunnel para prevenir abuso

**Solução:**
- Clique em "Continue" na primeira vez
- Ou use ngrok/Cloudflare para evitar essa página

---

### Problema: "Endpoint não encontrado - verifique a versão do backend"

**Causas possíveis:**
- Versão do backend desatualizada
- Endpoint foi renomeado ou removido
- URL do túnel aponta para serviço errado

**Soluções:**

1. Verifique se o endpoint existe:
```bash
curl http://localhost:8000/api/health
```

2. Liste todos os endpoints disponíveis:
```bash
curl http://localhost:8000/docs
# Acesse no navegador para ver documentação interativa
```

3. Atualize o backend:
```bash
cd backend
git pull
pip install -r requirements.txt
```

---

### Problema: Conexão lenta ou timeout

**Causas possíveis:**
- Latência do túnel
- Backend sobrecarregado
- Rede instável

**Soluções:**

1. Escolha região mais próxima (ngrok):
```bash
ngrok http 8000 --region us  # ou eu, ap, au, sa, jp, in
```

2. Aumente timeout no frontend (se necessário):
```javascript
// Em api.js
const response = await fetch(url, {
  ...options,
  signal: AbortSignal.timeout(10000) // 10 segundos
})
```

3. Use Cloudflare Tunnel para melhor performance global

---

## Checklist de Deployment

Use este checklist para garantir que tudo está configurado corretamente:

### Backend Local

- [ ] Backend está rodando em `http://localhost:8000`
- [ ] Endpoint `/api/health` retorna `{"status":"ok"}`
- [ ] Arquivo `backend/.env` existe e contém `CORS_ORIGINS`
- [ ] `CORS_ORIGINS` inclui URL do Vercel
- [ ] Logs mostram: `[CORS] Configured origins: [...]`
- [ ] Socket.io está configurado com mesmas origens CORS

### Túnel

- [ ] Serviço de túnel escolhido (ngrok/localtunnel/Cloudflare)
- [ ] Túnel está rodando e acessível
- [ ] URL do túnel responde a requisições HTTP
- [ ] Teste manual: `curl https://sua-url/api/health` retorna sucesso
- [ ] WebSocket funciona (se aplicável)

### Frontend no Vercel

- [ ] Deploy no Vercel concluído com sucesso
- [ ] URL do Vercel anotada (ex: `https://seu-app.vercel.app`)
- [ ] Acesso ao painel administrativo: `https://seu-app.vercel.app/admin/config`
- [ ] URL do túnel configurada no painel
- [ ] Status de conexão mostra "Conectado" (verde)
- [ ] Teste de funcionalidade: fazer uma requisição à API

### Testes de Integração

- [ ] Requisições HTTP funcionam (ex: listar tasks)
- [ ] WebSocket conecta e recebe eventos
- [ ] Erros são exibidos corretamente
- [ ] Reconexão automática funciona ao mudar URL
- [ ] Logs de erro incluem timestamps

### Documentação

- [ ] URL do túnel documentada para o time
- [ ] Instruções de como reiniciar o túnel
- [ ] Contato para troubleshooting definido

---

## Dicas Adicionais

### Manter túnel rodando em background

**ngrok:**
```bash
# Linux/macOS
nohup ngrok http 8000 &

# Windows (PowerShell)
Start-Process ngrok -ArgumentList "http 8000" -WindowStyle Hidden
```

**localtunnel:**
```bash
# Linux/macOS
nohup lt --port 8000 &

# Windows (PowerShell)
Start-Process lt -ArgumentList "--port 8000" -WindowStyle Hidden
```

### Automatizar inicialização

Crie um script `start-tunnel.sh` (Linux/macOS):

```bash
#!/bin/bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
sleep 3
ngrok http 8000
```

Ou `start-tunnel.bat` (Windows):

```batch
@echo off
cd backend
start /B python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
timeout /t 3
ngrok http 8000
```

### Monitoramento

**ngrok:**
- Interface web: `http://127.0.0.1:4040`
- API: `http://127.0.0.1:4040/api/tunnels`

**Cloudflare:**
```bash
cloudflared tunnel info meu-backend
```

### Segurança

1. **Não exponha dados sensíveis** através do túnel
2. **Use HTTPS** sempre que possível (ngrok e Cloudflare fornecem automaticamente)
3. **Limite CORS** apenas às origens necessárias
4. **Monitore logs** para detectar acessos suspeitos
5. **Desative o túnel** quando não estiver em uso

---

## Recursos Adicionais

- [Documentação ngrok](https://ngrok.com/docs)
- [Documentação localtunnel](https://github.com/localtunnel/localtunnel)
- [Documentação Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/)
- [Socket.io CORS](https://socket.io/docs/v4/handling-cors/)

---

## Suporte

Se você encontrar problemas não cobertos neste guia:

1. Verifique os logs do backend: `backend/logs/`
2. Verifique o console do navegador (F12)
3. Teste a conexão manualmente com `curl`
4. Consulte a documentação do serviço de túnel
5. Entre em contato com o time de desenvolvimento

---

**Última atualização:** 2024-01-15
