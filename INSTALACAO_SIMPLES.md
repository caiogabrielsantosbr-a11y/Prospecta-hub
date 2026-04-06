# 🚀 Instalação Simples - Rodar Localmente

Guia para rodar o Prospecta HUB localmente usando o banco de dados existente.

## ✅ O que precisa instalar (apenas 2 coisas!)

### 1. Python 3.11 ou superior
- **Baixar**: https://www.python.org/downloads/
- **⚠️ IMPORTANTE**: Marcar "Add Python to PATH" durante instalação
- **Testar**: Abra o terminal e digite `python --version`

### 2. Node.js 18 ou superior  
- **Baixar**: https://nodejs.org/
- **Testar**: Abra o terminal e digite `node --version`

**Pronto! Só isso mesmo.** 🎉

---

## 📥 Passo a Passo

### 1. Extrair o Projeto

Extraia o arquivo ZIP que você recebeu em uma pasta qualquer.

Exemplo: `C:\Projetos\Prospecta-hub\`

### 2. Verificar os Arquivos .env

Os arquivos `.env` já devem estar incluídos no ZIP:
- `backend/.env` ✅
- `frontend/.env` ✅

Se não estiverem, peça ao dono do projeto.

### 3. Instalar Dependências

Abra o terminal na pasta do projeto e execute:
```bash
install.bat
```

Isso vai:
- Criar ambiente virtual Python
- Instalar todas as dependências Python
- Instalar navegador Chromium (Playwright)
- Instalar todas as dependências Node.js

**Aguarde ~10-15 minutos** (só precisa fazer isso 1 vez!)

### 4. Executar o Projeto

```bash
start.bat
```

O navegador vai abrir automaticamente em http://localhost:5173

---

## ⏱️ Tempo de Instalação

- **Primeira vez**: ~10-15 minutos
  - Python: 2 min
  - Node.js: 2 min  
  - Dependências: 5-10 min
  - Playwright: 2-3 min

- **Próximas vezes**: Apenas executar `start.bat` (instantâneo)

---

## 📦 O que será instalado automaticamente

### Backend (Python)
- FastAPI - Framework web
- Playwright - Automação navegador (Google Maps)
- Supabase - Cliente banco de dados
- Outras bibliotecas necessárias

### Frontend (React)
- React - Interface
- Vite - Build tool
- Supabase JS - Cliente banco
- Outras bibliotecas necessárias

**Total**: ~500MB de dependências

---

## ❌ Problemas Comuns

### "Python não encontrado"
**Solução**: Reinstale Python marcando "Add Python to PATH"

### "Node não encontrado"  
**Solução**: Reinstale Node.js

### "playwright install falhou"
**Solução**: Execute manualmente:
```bash
cd backend
venv\Scripts\activate
python -m playwright install chromium
```

### "Porta 8000 já em uso"
**Solução**: Feche outros programas ou mude a porta no `backend/.env`:
```env
BACKEND_PORT=8001
```

### "Erro de conexão com Supabase"
**Solução**: Verifique se o arquivo `.env` tem as credenciais corretas

---

## 🔄 Atualizar o Projeto

Quando receber uma nova versão:

1. Extraia o novo ZIP
2. Execute `install.bat` novamente (para atualizar dependências)
3. Execute `start.bat`

---

## 🎯 Resumo Ultra-Rápido

1. Instalar Python 3.11+ (com PATH)
2. Instalar Node.js 18+
3. Extrair ZIP do projeto
4. Executar `install.bat`
5. Executar `start.bat`
6. Acessar http://localhost:5173

**Pronto!** ✅

---

## 📞 Precisa de Ajuda?

- Verifique se Python e Node estão instalados: `python --version` e `node --version`
- Verifique se os arquivos `.env` existem nas pastas backend e frontend
- Leia os erros no terminal - geralmente indicam o problema
- Entre em contato: caiogabrielsantosbr@gmail.com
