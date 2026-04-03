/**
 * Facebook ADS Extractor Page
 */
import { useState } from 'react'
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
    <div className="p-8 space-y-8 max-w-[1600px]">
      <div className="flex flex-col gap-1">
        <span className="text-primary font-bold text-[10px] tracking-[0.15em] uppercase">MÓDULO</span>
        <h2 className="font-condensed text-4xl font-bold">Facebook ADS</h2>
        <p className="text-on-surface-variant text-sm">Extraia leads da Biblioteca de Anúncios do Facebook em 2 etapas.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Step 1: Feed */}
        <div className="glass-card p-8 rounded-lg space-y-6">
          <div className="flex items-center gap-3">
            <span className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold text-sm">1</span>
            <h4 className="text-lg font-bold">Buscar Feed</h4>
          </div>
          <p className="text-sm text-on-surface-variant">Busque anúncios por palavra-chave na Ads Library.</p>
          <div className="space-y-2">
            <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">Palavra-chave</label>
            <input type="text" value={keyword} onChange={(e) => setKeyword(e.target.value)} placeholder="ex: e-commerce fashion" className="w-full" />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">Delay (ms)</label>
            <input type="number" value={delay} onChange={(e) => setDelay(parseInt(e.target.value))} className="w-32" />
          </div>
          <button onClick={handleStartFeed} className="btn-primary">
            <span className="material-symbols-outlined text-lg">search</span>
            Buscar Feed
          </button>
        </div>

        {/* Step 2: Contacts */}
        <div className="glass-card p-8 rounded-lg space-y-6">
          <div className="flex items-center gap-3">
            <span className="w-8 h-8 rounded-lg bg-secondary/20 flex items-center justify-center text-secondary font-bold text-sm">2</span>
            <h4 className="text-lg font-bold">Extrair Contatos</h4>
          </div>
          <p className="text-sm text-on-surface-variant">Com o feed coletado, extraia emails, telefones e Instagram de cada página.</p>
          <button onClick={handleStartContacts} className="btn-primary">
            <span className="material-symbols-outlined text-lg">contact_page</span>
            Extrair Contatos
          </button>
        </div>
      </div>

      {/* Task Status */}
      {currentTask && (
        <div className="glass-card p-6 rounded-lg">
          <div className="flex items-center gap-4 mb-4">
            <span className={`w-2 h-2 rounded-full ${currentTask.status === 'running' ? 'bg-primary animate-pulse' : 'bg-green-500'}`} />
            <span className="text-sm font-bold">{currentTask.module} — {currentTask.status}</span>
            <span className="text-xs text-on-surface-variant">#{currentTask.id}</span>
          </div>
          <div className="w-full h-2 bg-surface-container rounded-full overflow-hidden">
            <div className="h-full bg-primary transition-all duration-500" style={{ width: `${currentTask.progress}%` }} />
          </div>
          <div className="mt-4 font-mono text-[10px] space-y-1 max-h-20 overflow-y-auto custom-scrollbar">
            {(currentTask.logs || []).slice(-5).map((log, i) => (
              <div key={i} className="flex gap-2">
                <span className="text-on-surface-variant">{log.time}</span>
                <span className={`${log.level === 'error' ? 'text-error' : 'text-primary'}`}>{log.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
