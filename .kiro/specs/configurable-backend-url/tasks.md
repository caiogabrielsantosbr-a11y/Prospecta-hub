# Implementation Plan: Configurable Backend URL

## Overview

Esta implementação permite que o frontend React hospedado no Vercel se conecte dinamicamente a um backend FastAPI local através de configuração runtime. O sistema usa Supabase para persistência da configuração, suporta túneis reversos (ngrok, localtunnel, Cloudflare), e reconecta automaticamente conexões HTTP e WebSocket ao alterar a URL.

## Tasks

- [x] 1. Criar tabela app_settings no Supabase
  - Criar migration SQL com tabela app_settings (id, key, value, created_at, updated_at)
  - Adicionar índice único na coluna key
  - Executar migration no Supabase Dashboard ou via CLI
  - _Requirements: 9.1, 9.4_

- [x] 2. Instalar dependências do Supabase no frontend
  - Executar `npm install @supabase/supabase-js` no diretório frontend
  - Verificar que variáveis VITE_SUPABASE_URL e VITE_SUPABASE_KEY existem no .env
  - _Requirements: 9.1_

- [x] 3. Implementar Configuration Store (Zustand)
  - [x] 3.1 Criar arquivo frontend/src/store/useConfigStore.js
    - Implementar store Zustand com estado: apiUrl, connectionStatus, lastTested, isLoading
    - Implementar ação loadFromSupabase() que busca configuração da tabela app_settings
    - Implementar cache em sessionStorage com TTL de 5 minutos
    - Implementar ação setApiUrl() que valida, salva no Supabase (upsert), atualiza cache, e testa conexão
    - Implementar ação clearApiUrl() que deleta do Supabase e limpa cache
    - Implementar ação testConnection() que faz requisição GET para /api/health
    - Implementar função validateUrl() que verifica formato http:// ou https://
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.6, 9.1, 9.2, 9.3, 9.4, 9.6_
  
  - [ ]* 3.2 Escrever property test para validação de URL
    - **Property 1: URL Validation**
    - **Valida: Requirements 1.6, 2.3**
    - Gerar strings aleatórias e URLs válidas
    - Verificar que validateUrl retorna true apenas para URLs com http:// ou https://
  
  - [ ]* 3.3 Escrever property test para persistência round-trip
    - **Property 2: Configuration Persistence Round-Trip**
    - **Valida: Requirements 1.4, 9.1, 9.2**
    - Gerar URLs válidas aleatórias
    - Verificar que salvar no Supabase e carregar retorna o mesmo valor
  
  - [ ]* 3.4 Escrever property test para limpeza de configuração
    - **Property 6: Configuration Clear Removes Storage**
    - **Valida: Requirements 9.3**
    - Para qualquer URL configurada, clearApiUrl deve remover do Supabase

- [x] 4. Refatorar HTTP API Client
  - [x] 4.1 Modificar frontend/src/services/api.js
    - Importar useConfigStore
    - Criar método getBaseUrl() que lê apiUrl do store
    - Modificar método request() para usar ${baseUrl}/api${path}
    - Adicionar validação: lançar erro se apiUrl não configurada
    - Adicionar tratamento de erros específicos: 404, 500, timeout, CORS
    - Adicionar timestamp em todos os logs de erro
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 10.1, 10.2, 10.4, 10.5, 10.6_
  
  - [ ]* 4.2 Escrever property test para construção de URL
    - **Property 3: URL Prefix Application**
    - **Valida: Requirements 3.3, 3.5**
    - Gerar URLs base e paths de endpoint aleatórios
    - Verificar concatenação correta: baseUrl + /api + path
  
  - [ ]* 4.3 Escrever property test para efeito imediato de URL
    - **Property 5: Immediate URL Effect**
    - **Valida: Requirements 3.6**
    - Após atualizar apiUrl, próxima requisição deve usar nova URL
  
  - [ ]* 4.4 Escrever testes unitários para tratamento de erros
    - Testar erro quando apiUrl não configurada
    - Testar mensagens específicas para 404, 500, timeout, CORS
    - Verificar que timestamp é incluído nos logs

- [x] 5. Refatorar WebSocket Hook
  - [x] 5.1 Modificar frontend/src/hooks/useWebSocket.js
    - Importar useConfigStore e ler apiUrl
    - Adicionar condicional: não conectar se apiUrl for null
    - Passar apiUrl como primeiro argumento de io()
    - Adicionar apiUrl como dependência do useEffect para reconexão
    - Atualizar connectionStatus do store nos eventos connect, connect_error, disconnect
    - Manter configurações existentes: transports, reconnectionAttempts, reconnectionDelay
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_
  
  - [ ]* 5.2 Escrever property test para reconexão ao mudar URL
    - **Property 4: Configuration Change Triggers Reconnection**
    - **Valida: Requirements 1.5, 4.3, 4.4**
    - Ao mudar de uma URL válida para outra, deve desconectar e reconectar
  
  - [ ]* 5.3 Escrever testes unitários para WebSocket
    - Testar que não conecta quando apiUrl é null
    - Testar que reconecta quando apiUrl muda
    - Verificar que configurações de reconnection são mantidas

- [x] 6. Criar Admin Configuration Panel
  - [x] 6.1 Criar arquivo frontend/src/pages/AdminConfigPage.jsx
    - Criar componente funcional com estado local: inputUrl, error, isSaving
    - Ler apiUrl e connectionStatus do useConfigStore
    - Implementar handleSave: validar, chamar setApiUrl, exibir toast de sucesso/erro
    - Implementar handleClear: chamar clearApiUrl, limpar inputUrl
    - Renderizar campo de entrada para URL
    - Renderizar indicador de status (conectado/desconectado/testando/não configurado)
    - Renderizar botões "Salvar e Testar" e "Limpar Configuração"
    - Renderizar lista de exemplos clicáveis (ngrok, localtunnel, Cloudflare, IP local)
    - Renderizar mensagem de ajuda sobre como usar túneis
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_
  
  - [ ]* 6.2 Escrever property test para validação de URL inválida
    - **Property 12: Invalid URL Shows Error**
    - **Valida: Requirements 2.4**
    - URLs inválidas devem exibir erro e prevenir save
  
  - [ ]* 6.3 Escrever property test para URL válida aciona save e teste
    - **Property 13: Valid URL Triggers Save and Test**
    - **Valida: Requirements 2.5**
    - URLs válidas devem salvar e iniciar teste de conexão

- [x] 7. Criar Connection Status Component
  - [x] 7.1 Criar arquivo frontend/src/components/ConnectionStatus.jsx
    - Ler connectionStatus e isConfigured do useConfigStore
    - Renderizar badge com cor e ícone baseado no status
    - Exibir "Backend não configurado" se não configurado
    - Exibir "Conectado" (verde), "Desconectado" (vermelho), "Testando..." (azul)
    - _Requirements: 2.2, 6.4_
  
  - [x] 7.2 Adicionar ConnectionStatus ao header/navbar da aplicação
    - Importar e renderizar ConnectionStatus em componente de layout principal
    - Posicionar de forma discreta (canto superior direito)
    - _Requirements: 6.4_

- [x] 8. Adicionar rota para Admin Panel
  - [x] 8.1 Modificar frontend/src/App.jsx
    - Importar AdminConfigPage
    - Adicionar rota /admin/config para AdminConfigPage
    - Adicionar link de navegação para Admin Config no menu/sidebar
    - _Requirements: 2.8_
  
  - [x] 8.2 Inicializar configuração no App startup
    - Chamar loadFromSupabase() no useEffect do App.jsx
    - Garantir que configuração é carregada antes de renderizar rotas
    - _Requirements: 1.1, 1.2_

- [ ] 9. Atualizar configuração CORS no backend
  - [x] 9.1 Modificar backend/main.py
    - Ler variável de ambiente CORS_ORIGINS (padrão: "http://localhost:5173")
    - Fazer split por vírgula e strip de espaços para criar lista
    - Adicionar log: print(f"[CORS] Configured origins: {cors_origins}")
    - Passar lista para allow_origins do CORSMiddleware
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [ ]* 9.2 Escrever property test para parsing de CORS origins
    - **Property 7: CORS Origins Parsing**
    - **Valida: Requirements 5.2**
    - Gerar strings separadas por vírgula
    - Verificar que parsing cria array correto

- [ ] 10. Sincronizar CORS do Socket.io
  - [x] 10.1 Modificar backend/main.py (seção Socket.io)
    - Usar mesma variável cors_origins para cors_allowed_origins do AsyncServer
    - Remover wildcard "*" se existir
    - _Requirements: 5.6_
  
  - [ ]* 10.2 Escrever property test para consistência de CORS
    - **Property 8: CORS Policy Consistency**
    - **Valida: Requirements 5.6**
    - FastAPI e Socket.io devem ter mesma lista de origens

- [ ] 11. Implementar health check e teste de conexão
  - [x] 11.1 Verificar endpoint /api/health no backend
    - Confirmar que endpoint /api/health existe e retorna {"status": "ok"}
    - Se não existir, criar endpoint simples
    - _Requirements: 6.1, 6.2_
  
  - [ ]* 11.2 Escrever property test para health check automático
    - **Property 9: Health Check on Configuration**
    - **Valida: Requirements 6.1**
    - Ao configurar nova URL, deve fazer requisição para /api/health
  
  - [ ]* 11.3 Escrever testes unitários para feedback de conexão
    - Testar exibição de mensagem de sucesso quando health check passa
    - Testar exibição de erro quando health check falha
    - Testar sugestões de troubleshooting
    - _Requirements: 6.2, 6.3, 6.5, 6.6_

- [x] 12. Checkpoint - Testar integração completa
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Configurar deploy no Vercel
  - [x] 13.1 Criar arquivo vercel.json na raiz do projeto
    - Configurar buildCommand: "cd frontend && npm run build"
    - Configurar outputDirectory: "frontend/dist"
    - Configurar framework: "vite"
    - _Requirements: 7.1, 7.4_
  
  - [x] 13.2 Atualizar backend/.env.example
    - Documentar variável CORS_ORIGINS com exemplos
    - Incluir exemplo com URL do Vercel: "http://localhost:5173,https://your-app.vercel.app"
    - _Requirements: 5.1, 8.4_
  
  - [ ]* 13.3 Escrever property test para URL padrão do ambiente
    - **Property 10: Default URL from Environment**
    - **Valida: Requirements 7.3**
    - Se VITE_DEFAULT_API_URL definida e sem config no Supabase, usar valor da env
  
  - [ ]* 13.4 Escrever property test para timestamps em logs de erro
    - **Property 11: Error Logs Include Timestamps**
    - **Valida: Requirements 10.6**
    - Todos os logs de erro devem incluir timestamp

- [ ] 14. Criar documentação de túneis e troubleshooting
  - [x] 14.1 Criar arquivo docs/TUNNEL_SETUP.md
    - Documentar setup do ngrok com exemplos de comandos
    - Documentar setup do localtunnel com exemplos
    - Documentar setup do Cloudflare Tunnel com exemplos
    - Incluir seção de troubleshooting para problemas comuns
    - Documentar como configurar CORS_ORIGINS no backend
    - Incluir checklist de deployment
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_
  
  - [x] 14.2 Atualizar README.md principal
    - Adicionar seção sobre configuração runtime do backend
    - Linkar para docs/TUNNEL_SETUP.md
    - Incluir instruções de deploy no Vercel
    - _Requirements: 7.5, 7.6_

- [x] 15. Final checkpoint - Validação completa
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marcadas com `*` são opcionais (testes) e podem ser puladas para MVP mais rápido
- Cada task referencia requirements específicos para rastreabilidade
- Property tests validam propriedades universais de correção
- Unit tests validam exemplos específicos e casos extremos
- Checkpoints garantem validação incremental
- A configuração é salva no Supabase (tabela app_settings), não no localStorage
- sessionStorage é usado apenas como cache temporário para performance
