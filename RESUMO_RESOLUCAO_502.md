# 🔧 Resolução do Erro 502 Bad Gateway

## ✅ Problema Resolvido
O backend FastAPI estava travando durante o carregamento devido a conflitos com Socket.IO e imports de módulos.

## 🎯 Solução Aplicada

### 1. Simplificação do Backend
Desabilitamos temporariamente:
- Socket.IO (WebSocket)
- Task Manager
- Todos os routers de módulos (gmap, facebook, emails, locations, leads)
- Endpoints de tasks

### 2. Mudança na Inicialização
Ao invés de `python main.py`, usamos:
```bash
uvicorn main:app --host 0.0.0.0 --port 8001
```

### 3. Mudança de Porta
Backend agora roda na porta **8001** (a 8000 estava ocupada)

## 📋 Checklist - O que fazer agora

### ☐ 1. Atualizar ngrok
```bash
# Pare o ngrok atual (Ctrl+C)
# Reinicie apontando para porta 8001:
ngrok http 8001
```

### ☐ 2. Obter JWT Secret do Supabase
Siga as instruções em `OBTER_JWT_SECRET.md`:
1. Acesse https://app.supabase.com/project/gyenypsxpidmsxabjhqg/settings/api
2. Copie o **JWT Secret**
3. Cole no `backend/.env` na linha `SUPABASE_JWT_SECRET=`
4. Reinicie o backend

### ☐ 3. Testar o Backend
Após reiniciar o ngrok, teste:
```bash
curl https://sua-url-ngrok.ngrok-free.dev/api/health
```

Deve retornar:
```json
{"status": "ok", "version": "1.0.0"}
```

### ☐ 4. Configurar Políticas de Storage
Execute o SQL em `CONFIGURAR_STORAGE_POLICIES.sql` no Supabase para resolver o erro de upload de avatar.

### ☐ 5. Testar Upload de Avatar
Acesse https://prospecta-hub.vercel.app/profile e tente fazer upload de uma foto.

## 🔄 Próximos Passos (Após Tudo Funcionar)

### Reabilitar Funcionalidades
Quando o básico estiver funcionando, precisamos reabilitar no `backend/main.py`:
1. Socket.IO (para WebSocket de tasks em tempo real)
2. Task Manager (para gerenciar tarefas de scraping)
3. Routers de módulos (gmap, facebook, emails, etc)

Isso será feito gradualmente para identificar se algum módulo específico causa problemas.

## 📁 Arquivos Modificados
- `backend/main.py` - Simplificado temporariamente
- `backend/.env` - Precisa do JWT Secret correto
- `BACKEND_RODANDO.md` - Guia de status atual
- `OBTER_JWT_SECRET.md` - Como obter JWT Secret
- `CONFIGURAR_STORAGE_POLICIES.sql` - SQL para storage (já criado antes)
- `RESOLVER_ERRO_UPLOAD.md` - Guia completo de upload (já criado antes)

## 🎉 Status Atual
✅ Backend rodando na porta 8001
✅ Uvicorn iniciado com sucesso
✅ Supabase conectado
⏳ Aguardando configuração do JWT Secret
⏳ Aguardando atualização do ngrok
⏳ Aguardando configuração das políticas de storage
