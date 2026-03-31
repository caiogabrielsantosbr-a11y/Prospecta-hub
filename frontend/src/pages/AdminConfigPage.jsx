import { useState } from 'react'
import useConfigStore from '../store/useConfigStore'
import toast from 'react-hot-toast'

export default function AdminConfigPage() {
  const { apiUrl, connectionStatus, isLoading, setApiUrl, clearApiUrl } = useConfigStore()
  const [inputUrl, setInputUrl] = useState(apiUrl || '')
  const [error, setError] = useState(null)

  const examples = [
    { label: 'ngrok', url: 'https://abc123.ngrok.io' },
    { label: 'localtunnel', url: 'https://your-subdomain.loca.lt' },
    { label: 'Cloudflare', url: 'https://tunnel.example.com' },
    { label: 'Local IP', url: 'http://192.168.1.100:8000' },
  ]

  const handleSave = async () => {
    setError(null)
    
    try {
      await setApiUrl(inputUrl)
      toast.success('Configuração salva e conexão testada com sucesso!')
    } catch (e) {
      setError(e.message)
      toast.error('Falha ao salvar configuração')
    }
  }

  const handleClear = async () => {
    try {
      await clearApiUrl()
      setInputUrl('')
      setError(null)
      toast.success('Configuração limpa')
    } catch (e) {
      toast.error('Falha ao limpar configuração')
    }
  }

  const statusColors = {
    connected: 'text-primary',
    disconnected: 'text-error',
    testing: 'text-secondary',
    unconfigured: 'text-on-surface-variant',
  }

  const statusLabels = {
    connected: 'Conectado',
    disconnected: 'Desconectado',
    testing: 'Testando...',
    unconfigured: 'Não configurado',
  }

  return (
    <div className="p-8 space-y-8 max-w-[1200px]">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <span className="text-primary font-bold text-[10px] tracking-[0.15em] uppercase">SISTEMA</span>
        <h2 className="text-3xl font-bold tracking-tight">Configuração do Backend</h2>
        <p className="text-on-surface-variant text-sm mt-2">
          Configure a URL do backend para conectar o frontend aos serviços de extração.
        </p>
      </div>
      
      <div className="glass-card rounded-lg p-8 space-y-6">
        {/* Connection Status */}
        <div className="flex items-center justify-between p-4 rounded-lg bg-surface-container-high border border-outline-variant/20">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-on-surface-variant">cable</span>
            <span className="text-sm font-semibold">Status da Conexão</span>
          </div>
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${connectionStatus === 'connected' ? 'bg-primary animate-pulse' : connectionStatus === 'disconnected' ? 'bg-error' : 'bg-on-surface-variant'}`} />
            <span className={`text-sm font-bold ${statusColors[connectionStatus]}`}>
              {statusLabels[connectionStatus]}
            </span>
          </div>
        </div>

        {/* URL Input */}
        <div className="space-y-2">
          <label className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">
            URL do Backend
          </label>
          <input
            type="text"
            value={inputUrl}
            onChange={(e) => setInputUrl(e.target.value)}
            placeholder="https://abc123.ngrok.io"
            className="w-full !bg-surface-container-high !border-outline-variant/30 text-sm"
            disabled={isLoading}
          />
          {error && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-error/10 border border-error/30">
              <span className="material-symbols-outlined text-error text-sm">error</span>
              <p className="text-sm text-error">{error}</p>
            </div>
          )}
        </div>

        {/* Examples */}
        <div className="space-y-3">
          <label className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">
            Exemplos de URLs válidas
          </label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {examples.map((ex) => (
              <button
                key={ex.label}
                onClick={() => setInputUrl(ex.url)}
                className="flex items-center gap-2 p-3 rounded-lg bg-surface-container-high hover:bg-surface-container-highest border border-outline-variant/20 hover:border-primary/30 transition-all text-left"
                disabled={isLoading}
              >
                <span className="material-symbols-outlined text-primary text-sm">link</span>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-semibold text-on-surface">{ex.label}</div>
                  <div className="text-[10px] text-on-surface-variant truncate">{ex.url}</div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-4 border-t border-outline-variant/10">
          <button
            onClick={handleSave}
            disabled={isLoading || !inputUrl}
            className="btn-primary flex-1 justify-center disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                Salvando...
              </>
            ) : (
              <>
                <span className="material-symbols-outlined text-lg">save</span>
                Salvar e Testar
              </>
            )}
          </button>
          <button
            onClick={handleClear}
            disabled={isLoading}
            className="btn-ghost border-error/30 text-error hover:bg-error/10 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span className="material-symbols-outlined text-lg">delete</span>
            Limpar Configuração
          </button>
        </div>

        {/* Help Text */}
        <div className="bg-primary/10 p-4 rounded-lg border border-primary/20">
          <div className="flex gap-3">
            <span className="material-symbols-outlined text-primary text-xl">info</span>
            <div className="flex-1 space-y-2">
              <p className="text-sm font-semibold text-on-surface">Como usar:</p>
              <p className="text-sm text-on-surface-variant leading-relaxed">
                Execute seu backend local e exponha-o usando um serviço de túnel 
                (ngrok, localtunnel, Cloudflare Tunnel). Cole a URL pública aqui e clique em "Salvar e Testar".
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
