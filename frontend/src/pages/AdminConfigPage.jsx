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
    connected: 'text-green-600',
    disconnected: 'text-red-600',
    testing: 'text-yellow-600',
    unconfigured: 'text-gray-600',
  }

  const statusLabels = {
    connected: 'Conectado',
    disconnected: 'Desconectado',
    testing: 'Testando...',
    unconfigured: 'Não configurado',
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Configuração do Backend</h1>
      
      <div className="bg-white rounded-lg shadow p-6 space-y-6">
        {/* Connection Status */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Status da Conexão:</span>
          <span className={`text-sm font-semibold ${statusColors[connectionStatus]}`}>
            {statusLabels[connectionStatus]}
          </span>
        </div>

        {/* URL Input */}
        <div>
          <label className="block text-sm font-medium mb-2">
            URL do Backend
          </label>
          <input
            type="text"
            value={inputUrl}
            onChange={(e) => setInputUrl(e.target.value)}
            placeholder="https://abc123.ngrok.io"
            className="w-full px-3 py-2 border rounded-md"
            disabled={isLoading}
          />
          {error && (
            <p className="mt-2 text-sm text-red-600">{error}</p>
          )}
        </div>

        {/* Examples */}
        <div>
          <p className="text-sm font-medium mb-2">Exemplos de URLs válidas:</p>
          <div className="space-y-1">
            {examples.map((ex) => (
              <button
                key={ex.label}
                onClick={() => setInputUrl(ex.url)}
                className="block text-sm text-blue-600 hover:underline"
                disabled={isLoading}
              >
                {ex.label}: {ex.url}
              </button>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={handleSave}
            disabled={isLoading || !inputUrl}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {isLoading ? 'Salvando...' : 'Salvar e Testar'}
          </button>
          <button
            onClick={handleClear}
            disabled={isLoading}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 disabled:opacity-50"
          >
            Limpar Configuração
          </button>
        </div>

        {/* Help Text */}
        <div className="bg-blue-50 p-4 rounded-md">
          <p className="text-sm text-blue-900">
            <strong>Como usar:</strong> Execute seu backend local e exponha-o usando um serviço de túnel 
            (ngrok, localtunnel, Cloudflare Tunnel). Cole a URL pública aqui e clique em "Salvar e Testar".
          </p>
        </div>
      </div>
    </div>
  )
}
