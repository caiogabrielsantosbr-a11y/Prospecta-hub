---
description: Commit e push automático para o GitHub
---

# Push para GitHub

Suba todas as mudanças pendentes para o repositório GitHub.

## Passos

// turbo-all

1. Verifique se há mudanças pendentes:
```bash
git status
```

2. Se houver mudanças, adicione todas:
```bash
git add -A
```

3. Crie o commit com uma mensagem descritiva baseada nas mudanças feitas. Use o formato convencional:
```bash
git commit -m "tipo: descrição concisa das mudanças"
```
Tipos: `feat`, `fix`, `refactor`, `style`, `docs`, `chore`

4. Faça o push para o GitHub:
```bash
git push origin main
```

5. Confirme que o push foi bem-sucedido:
```bash
git log -n 1 --oneline
```

## Configuração do repositório
- **Repo:** https://github.com/caiogabrielsantosbr-a11y/Prospecta-hub
- **Autor:** caiogabrielsantosbr-a11y
- **Email:** caiogabrielsantosbr@gmail.com
- **Branch:** main
