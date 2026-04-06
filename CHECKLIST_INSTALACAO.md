# ✅ Checklist de Instalação - Prospecta HUB

## 📋 Pré-requisitos (instalar apenas 1 vez)

- [ ] **Python 3.11+** instalado
  - Link: https://www.python.org/downloads/
  - ⚠️ Marcar "Add Python to PATH"
  - Testar: `python --version`

- [ ] **Node.js 18+** instalado
  - Link: https://nodejs.org/
  - Testar: `node --version`

---

## 📥 Configuração Inicial (fazer 1 vez)

- [ ] Extrair o ZIP do projeto em uma pasta
- [ ] Verificar se os arquivos `.env` estão incluídos:
  - `backend/.env` ✅
  - `frontend/.env` ✅
- [ ] Executar `install.bat` (instala dependências)

---

## ▶️ Executar o Projeto (sempre que quiser usar)

- [ ] Abrir terminal na pasta do projeto
- [ ] Executar `start.bat`
- [ ] Aguardar abrir automaticamente
- [ ] Acessar: http://localhost:5173

---

## 🎯 Resumo Visual

```
┌─────────────────────────────────────────┐
│  1. Instalar Python (com PATH)         │
│     ↓                                   │
│  2. Instalar Node.js                    │
│     ↓                                   │
│  3. Extrair ZIP do projeto              │
│     ↓                                   │
│  4. Verificar se .env estão incluídos   │
│     ↓                                   │
│  5. Executar install.bat                │
│     ↓                                   │
│  6. Executar start.bat                  │
│     ↓                                   │
│  7. Usar o sistema! 🎉                  │
└─────────────────────────────────────────┘
```

---

## 📁 Arquivos .env (já devem estar no ZIP)

### backend/.env
```env
SUPABASE_URL=https://[projeto].supabase.co
SUPABASE_KEY=[chave_anon]
SUPABASE_SERVICE_KEY=[service_key]
JWT_SECRET=[chave_secreta]
```

### frontend/.env
```env
VITE_SUPABASE_URL=https://[projeto].supabase.co
VITE_SUPABASE_ANON_KEY=[chave_anon]
VITE_API_URL=http://localhost:8000
```

**✅ Se o ZIP foi enviado corretamente, esses arquivos já estão incluídos!**

---

## ⏱️ Tempo Estimado

| Etapa | Tempo |
|-------|-------|
| Instalar Python | 2 min |
| Instalar Node.js | 2 min |
| Extrair ZIP | 1 min |
| Verificar .env | 1 min |
| install.bat | 5-10 min |
| **TOTAL** | **~15 min** |

Depois disso, é só executar `start.bat` sempre que quiser usar!

---

## ❌ Se algo der errado

### Python não encontrado
→ Reinstale marcando "Add to PATH"

### Node não encontrado
→ Reinstale Node.js

### install.bat falhou
→ Verifique se Python e Node estão instalados

### start.bat não funciona
→ Verifique se os arquivos .env existem

### Erro de conexão
→ Verifique se as credenciais no .env estão corretas

---

## 🆘 Precisa de Ajuda?

1. Leia o arquivo `INSTALACAO_SIMPLES.md`
2. Verifique os erros no terminal
3. Entre em contato: caiogabrielsantosbr@gmail.com
