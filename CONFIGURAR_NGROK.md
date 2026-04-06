# 🌐 Como Configurar o Ngrok

O ngrok cria um túnel público para o seu backend local. Cada pessoa precisa ter sua própria conta.

---

## 📝 Passo a Passo

### 1. Criar Conta no Ngrok (GRÁTIS)

1. Acesse: https://ngrok.com/
2. Clique em "Sign up" (Cadastrar)
3. Crie sua conta (pode usar Google/GitHub)

### 2. Pegar seu Authtoken

1. Após fazer login, vá para: https://dashboard.ngrok.com/get-started/your-authtoken
2. Copie o authtoken (algo como: `2abc123def456ghi789jkl012mno345_6pqr789stu012vwx345yz`)

### 3. Configurar o Ngrok

**Opção 1 - Usar o script automático:**
```bash
configurar-ngrok.bat
```
Cole seu authtoken quando solicitado.

**Opção 2 - Configurar manualmente:**
```bash
ngrok config add-authtoken SEU_AUTHTOKEN_AQUI
```

### 4. Testar

Execute o backend:
```bash
start-backend.bat
```

O ngrok vai criar uma URL pública tipo:
```
https://abc123.ngrok-free.app
```

---

## 🔍 Como Ver a URL do Ngrok

### Método 1 - Interface Web do Ngrok
Abra no navegador: http://localhost:4040

Lá você verá:
- A URL pública do ngrok
- Todas as requisições HTTP
- Status da conexão

### Método 2 - Logs do Terminal
Quando você executa `start-backend.bat`, o ngrok mostra a URL no terminal.

### Método 3 - API do Ngrok
```bash
curl http://localhost:4040/api/tunnels
```

---

## ❌ Problemas Comuns

### "ERR_NGROK_108: You must sign up"
**Causa:** Ngrok não está autenticado
**Solução:** Execute `configurar-ngrok.bat` e cole seu authtoken

### "ERR_NGROK_105: Tunnel already exists"
**Causa:** Já existe um túnel rodando
**Solução:** Feche outros processos do ngrok ou reinicie o computador

### "Ngrok não inicia"
**Causa:** Arquivo ngrok.exe não existe ou está bloqueado
**Solução:** 
1. Baixe o ngrok: https://ngrok.com/download
2. Extraia o `ngrok.exe` na pasta raiz do projeto
3. Se o antivírus bloquear, adicione exceção

### "URL do ngrok não aparece"
**Causa:** Ngrok não está configurado ou não iniciou
**Solução:**
1. Verifique se o ngrok.exe existe na pasta do projeto
2. Execute `configurar-ngrok.bat`
3. Abra http://localhost:4040 no navegador

---

## 📦 Onde Baixar o Ngrok

Se o `ngrok.exe` não estiver no projeto:

1. Acesse: https://ngrok.com/download
2. Baixe a versão para Windows
3. Extraia o arquivo `ngrok.exe`
4. Coloque na pasta raiz do projeto (junto com `start-backend.bat`)

---

## 🆓 Plano Grátis do Ngrok

O plano grátis inclui:
- ✅ 1 túnel simultâneo
- ✅ URLs aleatórias (mudam a cada reinício)
- ✅ 40 conexões por minuto
- ✅ Sem limite de tempo

**Limitações:**
- ❌ URL muda toda vez que reinicia
- ❌ Não pode escolher o subdomínio

**Para URL fixa:** Upgrade para plano pago ($8/mês)

---

## 🔗 Links Úteis

- Dashboard: https://dashboard.ngrok.com/
- Documentação: https://ngrok.com/docs
- Status: https://status.ngrok.com/

---

## 💡 Dica

Se você quer que a URL do ngrok apareça automaticamente no terminal, adicione isso no final do `start-backend.bat`:

```batch
timeout /t 3 /nobreak >nul
echo.
echo ========================================
echo  URL DO NGROK
echo ========================================
curl -s http://localhost:4040/api/tunnels | findstr "public_url"
echo ========================================
```
