/**
 * Email Dispatch Page — Send bulk emails via SMTP.
 */
import { useState } from 'react'
import { api } from '../services/api'
import useTaskStore from '../store/useTaskStore'

const DEFAULT_TEMPLATE = `<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <h2 style="color: #333;">Olá, {{nome}}!</h2>
  <p>Espero que esteja bem.</p>
  <p>Gostaria de apresentar nossos serviços e como podemos ajudar o seu negócio a crescer.</p>
  <p>Podemos agendar uma conversa?</p>
  <br/>
  <p>Atenciosamente,<br/>Equipe Prospect</p>
</div>`

export default function EmailDispatchPage() {
  const [recipientsText, setRecipientsText] = useState('')
  const [subject, setSubject] = useState('{{nome}}, uma oportunidade para o seu negócio')
  const [template, setTemplate] = useState(DEFAULT_TEMPLATE)
  const [delay, setDelay] = useState(5)
  const [taskId, setTaskId] = useState(null)
  const [results, setResults] = useState([])

  const tasks = useTaskStore((s) => s.tasks)
  const currentTask = tasks.find(t => t.id === taskId)

  const handleStart = async () => {
    const lines = recipientsText.split('\n').filter(l => l.trim())
    const recipients = lines.map(line => {
      const parts = line.split(',').map(p => p.trim())
      return { email: parts[0], name: parts[1] || parts[0].split('@')[0] }
    }).filter(r => r.email.includes('@'))

    if (!recipients.length) return

    try {
      const res = await fetch('/api/dispatch/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ recipients, subject, template, delay }),
      })
      const data = await res.json()
      setTaskId(data.task_id)
    } catch (err) { console.error(err) }
  }

  const handleViewResults = async (tid) => {
    try {
      const res = await fetch(`/api/dispatch/results/${tid}`)
      const data = await res.json()
      setResults(data)
    } catch (err) { console.error(err) }
  }

  return (
    <div className="p-8 space-y-8 max-w-[1600px]">
      <div className="flex flex-col gap-1">
        <span className="text-primary font-bold text-[10px] tracking-[0.15em] uppercase">MÓDULO</span>
        <h2 className="font-condensed text-4xl font-bold">Disparo de Email</h2>
        <p className="text-on-surface-variant text-sm">Envie emails personalizados em massa via SMTP.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Config */}
        <div className="lg:col-span-2 glass-card p-8 rounded-lg space-y-6">
          <h4 className="text-lg font-bold">Campanha de Email</h4>

          <div className="space-y-2">
            <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
              Destinatários (email,nome — um por linha)
            </label>
            <textarea
              value={recipientsText}
              onChange={(e) => setRecipientsText(e.target.value)}
              placeholder="joao@empresa.com, João Silva&#10;maria@loja.com, Maria&#10;contato@site.com"
              rows={6}
              className="w-full resize-none font-mono text-sm"
            />
            <p className="text-[10px] text-on-surface-variant">
              {recipientsText.split('\n').filter(l => l.trim() && l.includes('@')).length} destinatários
            </p>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">Assunto</label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="w-full"
            />
            <p className="text-[10px] text-on-surface-variant">Use {'{{nome}}'} para personalizar</p>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">Template (HTML)</label>
            <textarea
              value={template}
              onChange={(e) => setTemplate(e.target.value)}
              rows={10}
              className="w-full resize-none font-mono text-xs"
            />
            <p className="text-[10px] text-on-surface-variant">
              Placeholders: {'{{nome}}'}, {'{{email}}'}
            </p>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">Delay entre envios (segundos)</label>
            <input type="number" value={delay} onChange={(e) => setDelay(parseInt(e.target.value))} className="w-32" min="1" />
          </div>

          <button onClick={handleStart} className="btn-primary">
            <span className="material-symbols-outlined text-lg">send</span>
            Iniciar Disparo
          </button>
        </div>

        {/* Status */}
        <div className="glass-card rounded-lg flex flex-col">
          <div className="p-6 border-b border-outline-variant/10">
            <h4 className="text-sm font-bold tracking-widest uppercase">Status do Disparo</h4>
          </div>
          {currentTask ? (
            <div className="p-6 space-y-4">
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${currentTask.status === 'running' ? 'bg-primary animate-pulse' : currentTask.status === 'completed' ? 'bg-green-500' : 'bg-error'}`} />
                <span className="text-xs font-bold uppercase">{currentTask.status}</span>
              </div>
              <div className="w-full h-2 bg-surface-container rounded-full overflow-hidden">
                <div className="h-full bg-primary transition-all duration-500" style={{ width: `${currentTask.progress}%` }} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-surface-container p-3 rounded-lg">
                  <p className="text-[10px] text-on-surface-variant uppercase">Enviados</p>
                  <p className="text-lg font-extrabold text-primary">{currentTask.stats.sent ?? 0}</p>
                </div>
                <div className="bg-surface-container p-3 rounded-lg">
                  <p className="text-[10px] text-on-surface-variant uppercase">Falhas</p>
                  <p className="text-lg font-extrabold text-error">{currentTask.stats.failed ?? 0}</p>
                </div>
                <div className="bg-surface-container p-3 rounded-lg">
                  <p className="text-[10px] text-on-surface-variant uppercase">Total</p>
                  <p className="text-lg font-extrabold">{currentTask.stats.total ?? 0}</p>
                </div>
                <div className="bg-surface-container p-3 rounded-lg">
                  <p className="text-[10px] text-on-surface-variant uppercase">Pendentes</p>
                  <p className="text-lg font-extrabold text-on-surface-variant">{currentTask.stats.pending ?? 0}</p>
                </div>
              </div>

              {currentTask.status === 'completed' && (
                <button onClick={() => handleViewResults(currentTask.id)} className="btn-ghost w-full justify-center">
                  <span className="material-symbols-outlined text-sm">visibility</span>
                  Ver Resultados
                </button>
              )}

              {/* Logs */}
              <div className="mt-2 font-mono text-[10px] space-y-1 max-h-32 overflow-y-auto custom-scrollbar">
                {(currentTask.logs || []).slice(-10).map((log, i) => (
                  <div key={i} className="flex gap-2">
                    <span className="text-on-surface-variant">{log.time}</span>
                    <span className={log.level === 'error' ? 'text-error' : 'text-primary'}>{log.message}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="p-6 flex-1 flex items-center justify-center">
              <p className="text-sm text-on-surface-variant">Configure SMTP no .env e inicie um disparo</p>
            </div>
          )}
        </div>
      </div>

      {/* Results Table */}
      {results.length > 0 && (
        <div className="glass-card rounded-lg overflow-hidden">
          <div className="p-6 border-b border-outline-variant/10">
            <h4 className="text-lg font-bold">Resultados ({results.length})</h4>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-outline-variant/10">
                  <th className="text-left p-4 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Email</th>
                  <th className="text-left p-4 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Nome</th>
                  <th className="text-left p-4 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Status</th>
                  <th className="text-left p-4 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Erro</th>
                </tr>
              </thead>
              <tbody>
                {results.map((r, i) => (
                  <tr key={i} className="border-b border-outline-variant/5 hover:bg-surface-container-low transition-colors">
                    <td className="p-4 font-mono text-xs">{r.email}</td>
                    <td className="p-4">{r.name}</td>
                    <td className="p-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${r.status === 'sent' ? 'bg-primary/10 text-primary' : 'bg-error/10 text-error'}`}>
                        {r.status === 'sent' ? 'ENVIADO' : 'FALHA'}
                      </span>
                    </td>
                    <td className="p-4 text-xs text-error">{r.error || '—'}</td>
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
