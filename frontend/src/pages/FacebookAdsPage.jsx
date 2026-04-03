/**
 * Facebook ADS Extractor Page
 */
import { useState } from 'react'
import { Search, UserCheck } from 'lucide-react'
import { api } from '../services/api'
import useTaskStore from '../store/useTaskStore'

export default function FacebookAdsPage() {
  const [keyword, setKeyword] = useState('')
  const [delay, setDelay] = useState(2000)
  const [taskId, setTaskId] = useState(null)
  const tasks = useTaskStore((s) => s.tasks)
  const currentTask = tasks.find(t => t.id === taskId)

  const handleStartFeed = async () => {
    if (!keyword) return
    const res = await api.startFacebookFeed(keyword, delay)
    setTaskId(res.task_id)
  }

  const handleStartContacts = async () => {
    const res = await api.startFacebookContacts(delay)
    setTaskId(res.task_id)
  }

  return (
    <div style={{ padding: 24 }}>
      {/* Two-Column Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
        {/* Step 1: Feed */}
        <div className="form-section" style={{ margin: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
            <div style={{
              width: 28, height: 28, borderRadius: 8,
              background: 'rgba(232,89,60,0.12)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'var(--pro-orange)', fontWeight: 700, fontSize: 13,
            }}>1</div>
            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--pro-text)' }}>Buscar Feed</div>
          </div>
          <div style={{ fontSize: 12, color: 'var(--pro-muted)', marginBottom: 14 }}>
            Busque anúncios por palavra-chave na Ads Library.
          </div>

          <div className="field-label">Palavra-chave</div>
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="ex: e-commerce fashion"
            style={{ width: '100%', marginBottom: 12 }}
          />

          <div className="field-label">Delay (ms)</div>
          <input
            type="number"
            value={delay}
            onChange={(e) => setDelay(parseInt(e.target.value))}
            style={{ width: 120, marginBottom: 14 }}
          />

          <button onClick={handleStartFeed} className="btn-primary" style={{ width: '100%', justifyContent: 'center' }}>
            <Search size={13} strokeWidth={2} />
            Buscar Feed
          </button>
        </div>

        {/* Step 2: Contacts */}
        <div className="form-section" style={{ margin: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
            <div style={{
              width: 28, height: 28, borderRadius: 8,
              background: 'rgba(196,24,90,0.12)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'var(--pro-pink)', fontWeight: 700, fontSize: 13,
            }}>2</div>
            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--pro-text)' }}>Extrair Contatos</div>
          </div>
          <div style={{ fontSize: 12, color: 'var(--pro-muted)', marginBottom: 14, lineHeight: 1.5 }}>
            Com o feed coletado, extraia emails, telefones e Instagram de cada página.
          </div>

          <button onClick={handleStartContacts} className="btn-primary" style={{ width: '100%', justifyContent: 'center' }}>
            <UserCheck size={13} strokeWidth={2} />
            Extrair Contatos
          </button>
        </div>
      </div>

      {/* Task Status */}
      {currentTask && (
        <div className="pro-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
            <span className={`status-dot ${currentTask.status === 'running' ? 'animate-pulse' : ''}`}
              style={{ background: currentTask.status === 'running' ? 'var(--pro-orange)' : 'var(--pro-success)' }} />
            <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--pro-text)' }}>
              {currentTask.module} — {currentTask.status}
            </span>
            <span className="pro-badge badge-neutral">#{currentTask.id}</span>
          </div>

          <div className="prog-bar" style={{ marginBottom: 10 }}>
            <div className="prog-fill" style={{ width: `${currentTask.progress}%` }} />
          </div>

          <div className="pro-terminal" style={{ padding: 10, maxHeight: 80, overflow: 'auto' }}>
            {(currentTask.logs || []).slice(-5).map((log, i) => (
              <div key={i} className="term-line" style={{ fontSize: 10 }}>
                [{log.time}] <span className="hl">{log.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
