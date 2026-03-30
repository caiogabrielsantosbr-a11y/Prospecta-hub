# Requirements Document

## Introduction

Esta funcionalidade permite que o frontend React hospedado no Vercel (produção) se conecte dinamicamente a um backend FastAPI rodando localmente na máquina do desenvolvedor. O sistema deve suportar configuração runtime da URL do backend através de um painel administrativo, permitindo conexões HTTP (API REST) e WebSocket (Socket.io) sem necessidade de rebuild do frontend.

## Glossary

- **Frontend**: Aplicação React + Vite + Tailwind CSS + Socket.io hospedada no Vercel
- **Backend**: Servidor FastAPI rodando localmente em http://localhost:8000
- **Admin_Panel**: Interface de configuração para definir a URL do backend
- **API_URL**: URL base do backend para requisições HTTP REST (ex: https://abc123.ngrok.io)
- **WebSocket_Connection**: Conexão Socket.io para atualizações em tempo real
- **Runtime_Config**: Configuração carregada dinamicamente no navegador sem rebuild
- **Tunnel_Service**: Serviço de túnel reverso (ngrok, localtunnel, Cloudflare Tunnel) que expõe o backend local
- **CORS_Policy**: Política de Cross-Origin Resource Sharing do backend
- **Config_Store**: Armazenamento no Supabase (tabela app_settings) da configuração do sistema

## Requirements

### Requirement 1: Runtime Configuration System

**User Story:** Como desenvolvedor, eu quero configurar a URL do backend em runtime, para que eu possa conectar o frontend em produção ao meu backend local sem rebuild.

#### Acceptance Criteria

1. THE Frontend SHALL carregar a configuração da API_URL do Supabase no momento da inicialização
2. WHEN nenhuma API_URL está configurada no Supabase, THE Frontend SHALL usar uma URL padrão vazia e exibir aviso de configuração pendente
3. THE Frontend SHALL permitir que a API_URL seja modificada a qualquer momento através do Admin_Panel
4. WHEN a API_URL é modificada, THE Frontend SHALL persistir a nova configuração no Supabase (tabela app_settings)
5. WHEN a API_URL é modificada, THE Frontend SHALL reconectar automaticamente todas as conexões HTTP e WebSocket
6. THE Frontend SHALL validar que a API_URL fornecida é uma URL válida (formato http:// ou https://)

### Requirement 2: Admin Configuration Panel

**User Story:** Como desenvolvedor, eu quero um painel administrativo para configurar a URL do backend, para que eu possa facilmente alternar entre diferentes túneis ou ambientes.

#### Acceptance Criteria

1. THE Admin_Panel SHALL exibir um campo de entrada para a API_URL atual
2. THE Admin_Panel SHALL exibir o status da conexão com o backend (conectado/desconectado)
3. WHEN o usuário submete uma nova API_URL, THE Admin_Panel SHALL validar o formato da URL
4. WHEN a validação falha, THE Admin_Panel SHALL exibir mensagem de erro descritiva
5. WHEN a validação é bem-sucedida, THE Admin_Panel SHALL salvar a configuração e testar a conexão
6. THE Admin_Panel SHALL exibir exemplos de URLs válidas (ngrok, localtunnel, IP local)
7. THE Admin_Panel SHALL permitir limpar a configuração e retornar ao estado padrão
8. THE Admin_Panel SHALL ser acessível através de uma rota protegida ou seção específica da aplicação

### Requirement 3: HTTP API Client Configuration

**User Story:** Como desenvolvedor, eu quero que todas as requisições HTTP usem a URL configurada, para que o frontend em produção acesse meu backend local.

#### Acceptance Criteria

1. THE Frontend SHALL criar um cliente HTTP centralizado que usa a API_URL do Config_Store
2. WHEN a API_URL não está configurada, THE Frontend SHALL exibir mensagem de erro ao tentar fazer requisições
3. THE Frontend SHALL adicionar a API_URL como prefixo para todas as requisições à API
4. WHEN uma requisição HTTP falha por erro de rede, THE Frontend SHALL exibir mensagem indicando problema de conexão com o backend
5. THE Frontend SHALL suportar requisições para endpoints relativos (ex: /api/tasks) usando a API_URL configurada
6. WHEN a API_URL é atualizada, THE Frontend SHALL usar a nova URL imediatamente nas próximas requisições

### Requirement 4: WebSocket Connection Configuration

**User Story:** Como desenvolvedor, eu quero que a conexão Socket.io use a URL configurada, para que eu receba atualizações em tempo real do meu backend local.

#### Acceptance Criteria

1. THE Frontend SHALL configurar o cliente Socket.io para usar a API_URL do Config_Store
2. WHEN a API_URL não está configurada, THE Frontend SHALL não tentar estabelecer conexão WebSocket
3. WHEN a API_URL é atualizada, THE Frontend SHALL desconectar a conexão Socket.io existente
4. WHEN a API_URL é atualizada, THE Frontend SHALL estabelecer nova conexão Socket.io com a nova URL
5. THE Frontend SHALL manter as configurações de reconnection e transports do Socket.io existentes
6. WHEN a conexão WebSocket falha, THE Frontend SHALL continuar tentando reconectar usando a API_URL configurada

### Requirement 5: Backend CORS Configuration

**User Story:** Como desenvolvedor, eu quero que o backend aceite requisições do Vercel, para que o frontend em produção possa se comunicar com meu backend local.

#### Acceptance Criteria

1. THE Backend SHALL ler a lista de origens permitidas da variável de ambiente CORS_ORIGINS
2. THE Backend SHALL aceitar múltiplas origens separadas por vírgula na CORS_Policy
3. THE Backend SHALL incluir a origem do Vercel (*.vercel.app) na CORS_Policy quando configurada
4. THE Backend SHALL permitir credenciais (cookies, headers de autenticação) nas requisições CORS
5. THE Backend SHALL permitir todos os métodos HTTP (GET, POST, PUT, DELETE, PATCH) nas requisições CORS
6. THE Backend SHALL configurar o Socket.io server com cors_allowed_origins correspondente à CORS_Policy

### Requirement 6: Connection Health Check

**User Story:** Como desenvolvedor, eu quero verificar se a conexão com o backend está funcionando, para que eu saiba se a configuração está correta.

#### Acceptance Criteria

1. WHEN o usuário configura uma nova API_URL, THE Frontend SHALL fazer uma requisição de teste ao endpoint /api/health
2. WHEN a requisição de teste é bem-sucedida, THE Frontend SHALL exibir mensagem de sucesso
3. WHEN a requisição de teste falha, THE Frontend SHALL exibir mensagem de erro com detalhes
4. THE Frontend SHALL exibir indicador visual do status da conexão (conectado/desconectado) na interface
5. THE Frontend SHALL testar tanto a conexão HTTP quanto WebSocket ao validar a configuração
6. WHEN o backend está inacessível, THE Frontend SHALL sugerir verificar o Tunnel_Service e configuração de CORS

### Requirement 7: Vercel Deployment Configuration

**User Story:** Como desenvolvedor, eu quero fazer deploy do frontend no Vercel, para que ele fique acessível publicamente e possa se conectar ao meu backend local.

#### Acceptance Criteria

1. THE Frontend SHALL ser configurado para build no Vercel usando o comando "npm run build"
2. THE Frontend SHALL incluir variável de ambiente VITE_DEFAULT_API_URL no Vercel (opcional)
3. WHEN VITE_DEFAULT_API_URL está definida, THE Frontend SHALL usar esse valor como API_URL padrão inicial
4. THE Frontend SHALL funcionar corretamente sem variáveis de ambiente obrigatórias (configuração via Admin_Panel)
5. THE Frontend SHALL incluir instruções de deploy no README ou documentação
6. THE Frontend SHALL ser conectado ao repositório GitHub para deploy automático

### Requirement 8: Tunnel Service Documentation

**User Story:** Como desenvolvedor, eu quero documentação sobre como expor meu backend local, para que eu possa configurar o túnel corretamente.

#### Acceptance Criteria

1. THE Documentation SHALL incluir exemplos de uso do ngrok para expor o backend
2. THE Documentation SHALL incluir exemplos de uso do localtunnel para expor o backend
3. THE Documentation SHALL incluir exemplos de uso do Cloudflare Tunnel para expor o backend
4. THE Documentation SHALL explicar como configurar CORS_ORIGINS no backend com a URL do Vercel
5. THE Documentation SHALL incluir troubleshooting para problemas comuns de conexão
6. THE Documentation SHALL explicar como testar a configuração localmente antes do deploy

### Requirement 9: Configuration Persistence

**User Story:** Como desenvolvedor, eu quero que minha configuração seja salva no Supabase, para que ela seja compartilhada entre todos os usuários e dispositivos.

#### Acceptance Criteria

1. THE Frontend SHALL salvar a API_URL na tabela app_settings do Supabase
2. WHEN o usuário recarrega a página, THE Frontend SHALL restaurar a API_URL do Supabase
3. WHEN o usuário limpa a configuração, THE Frontend SHALL remover a API_URL do Supabase
4. THE Frontend SHALL usar a chave "backend_api_url" na tabela app_settings
5. WHEN o Supabase não está disponível, THE Frontend SHALL exibir erro e não permitir salvar configuração
6. THE Frontend SHALL usar cache local (sessionStorage) para evitar múltiplas requisições ao Supabase durante a sessão

### Requirement 10: Error Handling and User Feedback

**User Story:** Como desenvolvedor, eu quero feedback claro sobre problemas de conexão, para que eu possa diagnosticar e corrigir rapidamente.

#### Acceptance Criteria

1. WHEN uma requisição HTTP falha por timeout, THE Frontend SHALL exibir mensagem "Backend não respondeu - verifique se o túnel está ativo"
2. WHEN uma requisição HTTP falha por CORS, THE Frontend SHALL exibir mensagem "Erro de CORS - adicione a URL do Vercel no CORS_ORIGINS do backend"
3. WHEN a conexão WebSocket falha, THE Frontend SHALL exibir aviso discreto sem bloquear a interface
4. WHEN o backend retorna erro 404, THE Frontend SHALL exibir mensagem "Endpoint não encontrado - verifique a versão do backend"
5. WHEN o backend retorna erro 500, THE Frontend SHALL exibir mensagem "Erro interno do backend - verifique os logs"
6. THE Frontend SHALL incluir timestamp nos logs de erro para facilitar debugging
