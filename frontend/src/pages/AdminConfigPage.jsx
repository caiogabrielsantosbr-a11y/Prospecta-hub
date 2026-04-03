/**
 * AdminConfigPage — Backend configuration page.
 */
import { useState, useEffect } from 'react'
import { Link2, Save, Trash2, AlertCircle } from 'lucide-react'
import useConfigStore from '../store/useConfigStore'
import { api } from '../services/api'
import toast from 'react-hot-toast'

export default function AdminConfigPage() {
  const { backendUrl, setBackendUrl, testConnection, wsConnected } = useConfigStore()
  const [url, setUrl] = useState(backendUrl)
  const [testing, setTesting] = useState(false)

  useEffect(() => { setUrl(backendUrl) }, [backendUrl])

  const handleSave = async () => {
    setTesting(true)
    try {
      setBackendUrl(url)
      await testConnection()
      toast.success('Conexão estabelecida com sucesso!')
    } catch (e) {
      toast.error('Falha na conexão: ' + (e.message || 'Timeout'))
    }
    setTesting(false)
  }

  const handleClear = () => {
    setUrl('')
    setBackendUrl('')
    toast('URL limpa', { icon: '🗑️' })
  }

  return (
    <div style={{
      flex: 1, display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', padding: 40,
    }}>
      {/* Eyebrow */}
      <div style={{
        fontSize: 10, letterSpacing: '0.15em', textTransform: 'uppercase',
        color: 'var(--pro-orange)', fontWeight: 700, marginBottom: 8, textAlign: 'center',
      }}>
        Sistema
      </div>

      {/* Title */}
      <div style={{
        fontSize: 32, fontWeight: 800, color: 'var(--pro-text)',
        marginBottom: 6, textAlign: 'center',
      }}>
        Configuração do Backend
      </div>

      {/* Subtitle */}
      <div style={{
        fontSize: 13, color: 'var(--pro-muted)', marginBottom: 32, textAlign: 'center',
      }}>
        Configure a URL do backend para conectar o frontend aos serviços de extração.
      </div>

      {/* Config Card */}
      <div style={{
        width: '100%', maxWidth: 480,
        background: 'var(--pro-surface2)', border: '0.5px solid var(--pro-border)',
        borderRadius: 14, padding: 24,
      }}>
        {/* Connection Status Row */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          paddingBottom: 16, marginBottom: 16, borderBottom: '0.5px solid var(--pro-border)',
        }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--pro-text)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Link2 size={14} strokeWidth={2} />
            Status da Conexão
          </div>
          <div style={{
            fontSize: 12, fontWeight: 600,
            color: wsConnected ? 'var(--pro-success)' : '#f87171',
            display: 'flex', alignItems: 'center', gap: 5,
          }}>
            <span style={{
              width: 6, height: 6, borderRadius: '50%',
              background: wsConnected ? 'var(--pro-success)' : '#f87171',
            }} />
            {wsConnected ? 'Conectado' : 'Desconectado'}
          </div>
        </div>

        {/* URL Field */}
        <div className="field-label">URL do Backend</div>
        <input
          type="text"
          value={url}
          onChange={e => setUrl(e.target.value)}
          placeholder="https://seu-backend.ngrok-free.dev"
          style={{
            width: '100%', fontFamily: 'monospace', fontSize: 12, marginBottom: 14,
          }}
        />

        {/* Buttons */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 10 }}>
          <button
            className="btn-primary"
            onClick={handleSave}
            disabled={testing}
            style={{ width: '100%', justifyContent: 'center' }}
          >
            <Save size={13} strokeWidth={2} />
            {testing ? 'Testando...' : 'Salvar e Testar'}
          </button>
          <button className="btn-danger" onClick={handleClear}>
            <Trash2 size={13} strokeWidth={2} />
            Limpar
          </button>
        </div>

        {/* Help Box */}
        <div className="help-box">
          <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--pro-muted)', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
            <AlertCircle size={13} strokeWidth={2} />
            Como usar
          </div>
          <div style={{ fontSize: 11, color: 'var(--pro-muted2)', lineHeight: 1.6 }}>
            Execute seu backend local e exponha-o usando um serviço de túnel (ngrok, localtunnel, Cloudflare Tunnel). Cole a URL pública aqui e clique em "Salvar e Testar".
          </div>
        </div>
      </div>
    </div>
  )
}
