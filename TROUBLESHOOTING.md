# 🔧 Troubleshooting - Prospecta HUB

Guia rápido para resolver problemas comuns.

---

## ❌ Problema: start-backend.bat abre e fecha rapidamente

### Causa Provável
O script está encontrando um erro e fechando antes de você conseguir ler.

### Solução

1. **Execute o diagnóstico primeiro:**
   ```bash
   diagnostico.bat
   ```
   Isso vai mostrar o que está faltando.

2. **Abra o terminal manualmente:**
   - Pressione `Win + R`
   - Digite `cmd` e pressione Enter
   - Navegue até a pasta do projeto:
     ```bash
     cd C:\caminho\para\Prospecta-hub
     ```
   - Execute o backend manualmente:
     ```bash
     cd backend
     venv\Scripts\activate
     python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
     ```
   - Agora você verá o erro completo!

3. **Erros Comuns:**

   **"Python não encontrado"**
   - Reinstale Python marcando "Add Python to PATH"
   - Teste: `python --version`

   **"venv não encontrado"**
   - Execute `install.bat` primeiro

   **"ModuleNotFoundError"**
   - As dependências não foram instaladas
   - Execute `install.bat` novamente

   **"Port 8000 already in use"**
   - Outra aplicação está usando a porta 8000
   - Feche outros programas ou mude a porta no `.env`

   **"No module named 'uvicorn'"**
   - O ambiente virtual não foi ativado corretamente
   - Execute manualmente:
     ```bash
     cd backend
     venv\Scripts\activate
     pip install -r requirements.txt
     ```

---

## ❌ Problema: Erro ao instalar dependências Python

### Solução

1. **Atualize o pip:**
   ```bash
   cd backend
   venv\Scripts\activate
   python -m pip install --upgrade pip
   ```

2. **Instale novamente:**
   ```bash
   pip install -r requirements.txt
   ```

---

## ❌ Problema: Playwright não instala

### Solução

1. **Instale manualmente:**
   ```bash
   cd backend
   venv\Scripts\activate
   python -m playwright install chromium
   ```

2. **Se falhar, instale com permissões de admin:**
   - Clique com botão direito em `cmd`
   - "Executar como administrador"
   - Execute os comandos acima

---

## ❌ Problema: Frontend não inicia

### Solução

1. **Verifique se Node.js está instalado:**
   ```bash
   node --version
   ```

2. **Reinstale dependências:**
   ```bash
   cd frontend
   npm install
   ```

3. **Limpe o cache:**
   ```bash
   cd frontend
   rmdir /s /q node_modules
   del package-lock.json
   npm install
   ```

---

## ❌ Problema: Erro de conexão com Supabase

### Solução

1. **Verifique se os arquivos .env existem:**
   - `backend\.env`
   - `frontend\.env`

2. **Verifique as credenciais:**
   - SUPABASE_URL deve começar com `https://`
   - SUPABASE_KEY deve ser uma string longa
   - Não deve ter espaços ou aspas extras

3. **Teste a conexão:**
   - Abra o navegador
   - Vá para `https://seu-projeto.supabase.co`
   - Verifique se o projeto está ativo

---

## ❌ Problema: "Access Denied" ou "Permission Denied"

### Solução

1. **Execute como Administrador:**
   - Clique com botão direito em `install.bat`
   - "Executar como administrador"

2. **Desative o antivírus temporariamente:**
   - Alguns antivírus bloqueiam scripts .bat
   - Adicione a pasta do projeto às exceções

---

## ❌ Problema: Porta 8000 já está em uso

### Solução

1. **Encontre o processo usando a porta:**
   ```bash
   netstat -ano | findstr :8000
   ```

2. **Mate o processo:**
   ```bash
   taskkill /PID [número_do_pid] /F
   ```

3. **Ou mude a porta:**
   - Edite `backend\.env`
   - Adicione: `BACKEND_PORT=8001`
   - Edite `start-backend.bat`
   - Mude `8000` para `8001`

---

## 📞 Ainda com problemas?

1. Execute `diagnostico.bat` e tire um print
2. Abra o terminal e execute os comandos manualmente
3. Copie a mensagem de erro completa
4. Entre em contato: caiogabrielsantosbr@gmail.com

---

## ✅ Checklist Rápido

- [ ] Python 3.11+ instalado (com PATH)
- [ ] Node.js 18+ instalado
- [ ] Executou `install.bat` com sucesso
- [ ] Arquivos `.env` existem e estão corretos
- [ ] Porta 8000 está livre
- [ ] Antivírus não está bloqueando
- [ ] Executando como Administrador (se necessário)
