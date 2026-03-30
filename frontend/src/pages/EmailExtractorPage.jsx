/**
 * Email Extractor Page — domain-based email extraction.
 */
import { useState } from 'react'
import { api } from '../services/api'
import useTaskStore from '../store/useTaskStore'

export default function EmailExtractorPage() {
  const [domainsText, setDomainsText] = useState('')
  const [delay, setDelay] = useState(1)
  const [proxy, setProxy] = useState('')
  const [taskId, setTaskId] = useState(null)
  const [results, setResults] = useState([])

  const tasks = useTaskStore((s) => s.tasks)
  const currentTask = tasks.find(t => t.id === taskId)
  const emailTasks = tasks.filter(t => t.module === 'emails')

  const handleStart = async () => {
    const domains = domainsText.split('\n').map(d => d.trim()).filter(Boolean)
    if (!domains.length) return

    try {
      const res = await api.startEmailExtraction(domains, delay, proxy || null)
      setTaskId(res.task_id)
    } catch (err) {
      console.error(err)
    }
  }

  const handleViewResults = async (tid) => {
    try {
      const data = await api.getEmailResults(tid)
      setResults(data)
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="p-8 space-y-8 max-w-[1600px]">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <span className="text-primary font-bold text-[10px] tracking-[0.15em] uppercase">MÓDULO</span>
        <h2 className="text-3xl font-bold tracking-tight">Extrator de Email</h2>
        <p className="text-on-surface-variant text-sm">Extraia emails de domínios via RDAP + scraping de páginas de contato.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Input Panel */}
        <div className="lg:col-span-2 glass-card p-8 rounded-lg space-y-6">
          <h4 className="text-lg font-bold">Configuração</h4>

          <div className="space-y-2">
            <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
              Domínios (um por linha)
            </label>
            <textarea
              value={domainsText}
              onChange={(e) => setDomainsText(e.target.value)}
              placeholder="exemplo.com.br&#10;outrodominio.com&#10;website.com.br"
              rows={10}
              className="w-full resize-none font-mono text-sm"
            />
            <p className="text-[10px] text-on-surface-variant">
              {domainsText.split('\n').filter(d => d.trim()).length} domínios carregados
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
                Delay (segundos)
              </label>
              <input
                type="number"
                min="0.5"
                step="0.5"
                value={delay}
                onChange={(e) => setDelay(parseFloat(e.target.value))}
                className="w-full"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
                Proxy (opcional)
              </label>
              <input
                type="text"
                value={proxy}
                onChange={(e) => setProxy(e.target.value)}
                placeholder="http://user:pass@host:port"
                className="w-full"
              />
            </div>
          </div>

          <button onClick={handleStart} className="btn-primary">
            <span className="material-symbols-outlined text-lg">play_arrow</span>
            Iniciar Extração
          </button>
        </div>

        {/* Status Panel */}
        <div className="glass-card rounded-lg flex flex-col">
          <div className="p-6 border-b border-outline-variant/10">
            <h4 className="text-sm font-bold tracking-widest uppercase">Status da Extração</h4>
          </div>

          {currentTask ? (
            <div className="p-6 space-y-4">
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${currentTask.status === 'running' ? 'bg-primary animate-pulse' : currentTask.status === 'completed' ? 'bg-green-500' : 'bg-error'}`} />
                <span className="text-xs font-bold uppercase">{currentTask.status}</span>
              </div>

              {/* Progress */}
              <div className="space-y-1">
                <div className="w-full h-2 bg-surface-container rounded-full overflow-hidden">
                  <div className="h-full bg-primary transition-all duration-500" style={{ width: `${Math.min(100, currentTask.progress || 0)}%` }} />
                </div>
                <p className="text-[10px] text-on-surface-variant text-right">{Math.min(100, Math.round(currentTask.progress || 0))}%</p>
              </div>

              {/* Quick Stats */}
              <div className="grid grid-cols-2 gap-3">
                <MiniStat label="Encontrados" value={currentTask.stats?.leads ?? 0} color="text-primary" />
                <MiniStat label="Erros" value={currentTask.stats?.errors ?? 0} color="text-error" />
                <MiniStat label="Fila" value={currentTask.stats?.queue ?? 0} color="text-on-surface-variant" />
                <MiniStat label="Concluídos" value={currentTask.stats?.done ?? 0} color="text-on-surface" />
              </div>

              {currentTask.status === 'completed' && (
                <button onClick={() => handleViewResults(currentTask.id)} className="btn-ghost w-full justify-center">
                  <span className="material-symbols-outlined text-sm">visibility</span>
                  Ver Resultados
                </button>
              )}
            </div>
          ) : (
            <div className="p-6 flex-1 flex items-center justify-center">
              <p className="text-sm text-on-surface-variant">Nenhuma tarefa ativa</p>
            </div>
          )}

          {/* History */}
          {emailTasks.length > 0 && (
            <div className="p-4 border-t border-outline-variant/10">
              <p className="text-[10px] font-bold text-on-surface-variant uppercase tracking-widest mb-2">Histórico</p>
              <div className="space-y-1 max-h-32 overflow-y-auto custom-scrollbar">
                {emailTasks.map(t => (
                  <div key={t.id} className="flex items-center justify-between text-[10px] py-1 cursor-pointer hover:text-primary transition-colors" onClick={() => handleViewResults(t.id)}>
                    <span className="font-mono">#{t.id}</span>
                    <span className={`${t.status === 'completed' ? 'text-primary' : 'text-on-surface-variant'}`}>{t.status}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Results Table */}
      {results.length > 0 && (
        <div className="glass-card rounded-lg overflow-hidden">
          <div className="p-6 border-b border-outline-variant/10 flex items-center justify-between">
            <h4 className="text-lg font-bold">Resultados ({results.length})</h4>
            <a href={`/api/emails/export/${taskId}?format=csv`} className="btn-ghost text-xs" download>
              <span className="material-symbols-outlined text-sm">download</span>
              Exportar CSV
            </a>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-outline-variant/10">
                  <th className="text-left p-4 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Domínio</th>
                  <th className="text-left p-4 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Email</th>
                  <th className="text-left p-4 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Fonte</th>
                </tr>
              </thead>
              <tbody>
                {results.map((r, i) => (
                  <tr key={i} className="border-b border-outline-variant/5 hover:bg-surface-container-low transition-colors">
                    <td className="p-4 font-mono text-xs">{r.domain}</td>
                    <td className="p-4 text-primary font-medium">{r.email}</td>
                    <td className="p-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${r.source === 'RDAP' ? 'bg-primary/10 text-primary' : 'bg-secondary/10 text-secondary'}`}>
                        {r.source}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

function MiniStat({ label, value, color }) {
  return (
    <div className="bg-surface-container p-3 rounded-lg">
      <p className="text-[10px] text-on-surface-variant uppercase tracking-wider">{label}</p>
      <p className={`text-lg font-extrabold ${color}`}>{value ?? 0}</p>
    </div>
  )
}
