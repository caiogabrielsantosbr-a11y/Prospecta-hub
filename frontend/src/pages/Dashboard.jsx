/**
 * Dashboard — main overview page with stats from Supabase + backend.
 */
import { useState, useEffect } from 'react'
import { api } from '../services/api'
import useTaskStore from '../store/useTaskStore'
import { leadsService, gsheetsService } from '../services/supabase'

export default function Dashboard() {
  const [backendStats, setBackendStats] = useState(null)
  const [leadStats, setLeadStats] = useState(null)
  const [sendStats, setSendStats] = useState(null)
  const tasks = useTaskStore((s) => s.tasks)
  const activeTasks = tasks.filter(t => t.status === 'running' || t.status === 'paused')

  const loadSupabaseStats = async () => {
    try {
      const [ls, ss] = await Promise.all([
        leadsService.getStats(),
        gsheetsService.getSendStats(),
      ])
      setLeadStats(ls)
      setSendStats(ss)
    } catch (e) {
      console.error('Stats error:', e)
    }
  }

  const loadBackendStats = async () => {
    try {
      const data = await api.getDashboardStats()
      setBackendStats(data)
    } catch (_) {}
  }

  useEffect(() => {
    loadSupabaseStats()
    loadBackendStats()
    const interval = setInterval(() => {
      loadSupabaseStats()
      loadBackendStats()
    }, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="p-8 space-y-8 max-w-[1600px]">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <span className="text-primary font-bold text-[10px] tracking-[0.15em] uppercase">SISTEMA OPERACIONAL</span>
        <h2 className="text-3xl font-bold tracking-tight">Painel de Controle</h2>
      </div>

      {/* Stat Cards — row 1 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          label="Total de Leads"
          value={leadStats?.total ?? '—'}
          icon="groups"
          color="text-primary"
        />
        <StatCard
          label="Com Email"
          value={leadStats?.with_email ?? '—'}
          icon="email"
          color="text-secondary"
        />
        <StatCard
          label="Com Telefone"
          value={leadStats?.with_phone ?? '—'}
          icon="phone"
          color="text-tertiary"
        />
        <StatCard
          label="Processos Ativos"
          value={activeTasks.length}
          icon="bolt"
          color="text-primary"
          bars
        />
      </div>

      {/* Stat Cards — row 2 (GSheets) */}
      {sendStats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <StatCard
            label="Enviados Hoje"
            value={sendStats.today}
            icon="today"
            color="text-primary"
          />
          <StatCard
            label="Enviados esta Semana"
            value={sendStats.week}
            icon="date_range"
            color="text-secondary"
          />
          <StatCard
            label="Enviados este Mês"
            value={sendStats.month}
            icon="calendar_month"
            color="text-tertiary"
          />
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Sources Distribution */}
        <div className="lg:col-span-2 glass-card p-8 rounded-lg">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h4 className="text-lg font-bold">Visão de Leads</h4>
              <p className="text-on-surface-variant text-sm">Qualidade do banco de dados</p>
            </div>
          </div>
          <div className="space-y-6">
            <SourceBar
              label="Com Telefone"
              value={leadStats?.with_phone ?? 0}
              total={leadStats?.total || 1}
              color="bg-primary"
            />
            <SourceBar
              label="Com Email"
              value={leadStats?.with_email ?? 0}
              total={leadStats?.total || 1}
              color="bg-secondary"
            />
            <SourceBar
              label="Com Website"
              value={leadStats?.with_website ?? 0}
              total={leadStats?.total || 1}
              color="bg-tertiary"
            />
            <SourceBar
              label="Sem Telefone"
              value={leadStats?.without_phone ?? 0}
              total={leadStats?.total || 1}
              color="bg-error"
            />
          </div>
        </div>

        {/* Intelligence Logs */}
        <div className="glass-card rounded-lg flex flex-col">
          <div className="p-6 border-b border-outline-variant/10 flex items-center justify-between">
            <h4 className="text-sm font-bold tracking-widest uppercase">Logs de Inteligência</h4>
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
          </div>
          <div className="flex-1 p-4 font-mono text-[10px] space-y-3 custom-scrollbar overflow-y-auto max-h-[300px]">
            {tasks.length > 0 ? (
              tasks.flatMap(t => t.logs || []).reverse().slice(0, 20).map((log, i) => (
                <div key={i} className="flex gap-3">
                  <span className="text-on-surface-variant shrink-0">{log.time}</span>
                  <span className={`${log.level === 'error' ? 'text-error' : log.level === 'success' ? 'text-primary' : 'text-secondary'}`}>
                    [{log.level === 'error' ? 'FALHA' : log.level === 'success' ? 'SUCESSO' : 'INFO'}]
                  </span>
                  <span className="text-on-surface/80">{log.message}</span>
                </div>
              ))
            ) : (
              <div className="flex gap-3">
                <span className="text-on-surface-variant shrink-0">—</span>
                <span className="text-on-surface-variant">[SISTEMA]</span>
                <span className="text-on-surface/80">Aguardando tarefas...</span>
              </div>
            )}
          </div>
          <div className="p-4 border-t border-outline-variant/10 bg-surface-container/50">
            <div className="flex items-center gap-2">
              <span className="text-primary text-xs">&gt;</span>
              <input
                type="text"
                className="!bg-transparent !border-none p-0 text-[10px] w-full focus:!ring-0 font-mono"
                placeholder="Executar comando..."
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ── Sub-Components ───────────────────────────────────────── */

function StatCard({ label, value, icon, color = 'text-primary', bars }) {
  return (
    <div className="glass-card p-6 rounded-lg relative overflow-hidden group hover:bg-surface-container-highest transition-all duration-500">
      <div className="absolute -right-4 -top-4 w-24 h-24 bg-primary/5 rounded-full blur-2xl group-hover:bg-primary/10 transition-all" />
      <div className="flex items-center justify-between mb-3">
        <p className="text-on-surface-variant text-xs font-semibold uppercase tracking-wider">{label}</p>
        <span className={`material-symbols-outlined text-xl ${color}`}>{icon}</span>
      </div>
      <div className="flex items-end justify-between">
        <h3 className="text-3xl font-extrabold tracking-tighter">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </h3>
        {bars && (
          <div className="flex gap-1 h-4 items-end">
            <div className="w-1 bg-primary/40 h-2 rounded-full" />
            <div className="w-1 bg-primary h-4 rounded-full" />
            <div className="w-1 bg-primary/60 h-3 rounded-full" />
            <div className="w-1 bg-primary/80 h-2 rounded-full" />
          </div>
        )}
      </div>
    </div>
  )
}

function SourceBar({ label, value, total, color }) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-xs font-semibold">
        <span className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${color}`} />
          {label}
        </span>
        <span>{value?.toLocaleString() ?? 0} ({pct}%)</span>
      </div>
      <div className="w-full h-2 bg-surface-container rounded-full overflow-hidden">
        <div className={`h-full ${color} transition-all duration-700`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}
