/**
 * Dashboard — redesigned with colorful branded cards
 */
import { useState, useEffect } from 'react'
import { api } from '../services/api'
import useTaskStore from '../store/useTaskStore'
import { leadsService, gsheetsService } from '../services/supabase'

export default function Dashboard() {
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
    try { await api.getDashboardStats() } catch (_) {}
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

  const total = leadStats?.total ?? 0
  const withPhone = leadStats?.with_phone ?? 0
  const withEmail = leadStats?.with_email ?? 0
  const withWebsite = leadStats?.with_website ?? 0

  return (
    <div className="content-wrapper space-y-5">

      {/* ── Row 1: Lead Stats ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14 }}>
        <MetricCard
          label="Total de Leads"
          value={total.toLocaleString()}
          icon="groups"
          gradient="linear-gradient(135deg,#0055ff18,#0055ff08)"
          iconColor="#0055ff"
          borderColor="#0055ff30"
          badge={<span style={{ fontSize: 10, color: '#16a34a', fontWeight: 700 }}>↑ atualizado</span>}
        />
        <MetricCard
          label="Com Telefone"
          value={withPhone.toLocaleString()}
          icon="phone"
          gradient="linear-gradient(135deg,#16a34a18,#16a34a08)"
          iconColor="#16a34a"
          borderColor="#16a34a30"
          badge={total > 0 ? <span style={{ fontSize: 10, color: '#16a34a', fontWeight: 700 }}>{Math.round(withPhone/total*100)}%</span> : null}
        />
        <MetricCard
          label="Com Email"
          value={withEmail.toLocaleString()}
          icon="email"
          gradient="linear-gradient(135deg,#7c3aed18,#7c3aed08)"
          iconColor="#7c3aed"
          borderColor="#7c3aed30"
          badge={total > 0 ? <span style={{ fontSize: 10, color: '#7c3aed', fontWeight: 700 }}>{Math.round(withEmail/total*100)}%</span> : null}
        />
        <MetricCard
          label="Processos Ativos"
          value={activeTasks.length}
          icon="bolt"
          gradient={activeTasks.length > 0 ? "linear-gradient(135deg,#f59e0b22,#f59e0b08)" : "linear-gradient(135deg,#33333318,#33333308)"}
          iconColor={activeTasks.length > 0 ? "#f59e0b" : "var(--pro-muted)"}
          borderColor={activeTasks.length > 0 ? "#f59e0b40" : "var(--pro-border)"}
          badge={activeTasks.length > 0 ? <span style={{ fontSize: 10, color: '#f59e0b', fontWeight: 700, display:'flex', alignItems:'center', gap:3 }}><span style={{width:6,height:6,borderRadius:'50%',background:'#f59e0b',display:'inline-block',animation:'pulse 1s infinite'}} />Rodando</span> : null}
        />
      </div>

      {/* ── Row 2: Send Stats ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14 }}>
        <MetricCard
          label="Enviados Hoje"
          value={(sendStats?.today ?? 0).toLocaleString()}
          icon="today"
          gradient="linear-gradient(135deg,#E8593C18,#E8593C08)"
          iconColor="#E8593C"
          borderColor="#E8593C30"
        />
        <MetricCard
          label="Esta Semana"
          value={(sendStats?.week ?? 0).toLocaleString()}
          icon="date_range"
          gradient="linear-gradient(135deg,#0891b218,#0891b208)"
          iconColor="#0891b2"
          borderColor="#0891b230"
        />
        <MetricCard
          label="Este Mês"
          value={(sendStats?.month ?? 0).toLocaleString()}
          icon="calendar_month"
          gradient="linear-gradient(135deg,#dc268018,#dc268008)"
          iconColor="#dc2680"
          borderColor="#dc268030"
        />
      </div>

      {/* ── Row 3: Quality + Logs ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>

        {/* Quality card */}
        <div className="pro-card" style={{ padding: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
            <span className="material-symbols-outlined" style={{ color: '#0055ff', fontSize: 22 }}>insights</span>
            <div>
              <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--pro-text)' }}>Qualidade da Base</div>
              <div style={{ fontSize: 12, color: 'var(--pro-muted)' }}>{total.toLocaleString()} leads no total</div>
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <QualityRow label="Com Telefone" value={withPhone} total={total} color="#16a34a" icon="phone" />
            <QualityRow label="Com Email" value={withEmail} total={total} color="#7c3aed" icon="email" />
            <QualityRow label="Com Website" value={withWebsite} total={total} color="#0891b2" icon="language" />
            <QualityRow label="Sem Telefone" value={(leadStats?.without_phone ?? 0)} total={total} color="#ef4444" icon="phone_disabled" />
          </div>
        </div>

        {/* Terminal */}
        <div className="pro-terminal" style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="term-head">
            <div className="term-dots">
              <div className="term-dot" style={{ background: '#dc2626' }} />
              <div className="term-dot" style={{ background: '#d97706' }} />
              <div className="term-dot" style={{ background: '#16a34a' }} />
            </div>
            <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--pro-text)', letterSpacing: '0.08em' }}>LOGS DE INTELIGÊNCIA</span>
            <div className="live-dot" style={{ marginLeft: 'auto' }} />
          </div>

          <div style={{ flex: 1, overflow: 'auto', minHeight: 140 }} className="custom-scrollbar">
            {tasks.length > 0 ? (
              tasks.flatMap(t => t.logs || []).slice(-20).reverse().map((log, i) => (
                <div key={i} className="term-line">
                  [{log.time}] <span className={`${log.level === 'error' ? 'text-red-400' : log.level === 'success' ? 'hl' : ''}`}>
                    {log.level === 'error' ? 'FALHA' : log.level === 'success' ? 'SUCESSO' : 'INFO'}
                  </span>: {log.message}
                </div>
              ))
            ) : (
              <>
                <div className="term-line">— [SISTEMA] Aguardando tarefas...</div>
                <div className="term-line">— [INFO] <span className="hl">Backend conectado</span></div>
                <div className="term-line">— [INFO] {activeTasks.length} processos na fila</div>
              </>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 10, paddingTop: 10, borderTop: '0.5px solid var(--pro-border)' }}>
            <span style={{ color: 'rgba(232,89,60,0.7)' }}>›</span>
            <input type="text" style={{ flex: 1, background: 'transparent', border: 'none', padding: 0, fontSize: 13, color: 'var(--pro-muted)', fontFamily: 'monospace', outline: 'none' }} placeholder="Executar comando..." />
            <div className="term-cursor" />
          </div>
        </div>
      </div>
    </div>
  )
}

/* ── Sub-components ── */

function MetricCard({ label, value, icon, gradient, iconColor, borderColor, badge }) {
  return (
    <div style={{
      background: gradient,
      border: `1px solid ${borderColor}`,
      borderRadius: 12,
      padding: '18px 20px',
      display: 'flex',
      flexDirection: 'column',
      gap: 10,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span className="material-symbols-outlined" style={{ color: iconColor, fontSize: 22, opacity: 0.85 }}>{icon}</span>
        {badge}
      </div>
      <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--pro-text)', lineHeight: 1 }}>{value}</div>
      <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--pro-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{label}</div>
    </div>
  )
}

function QualityRow({ label, value, total, color, icon }) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0
  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: 13, fontWeight: 600, color: 'var(--pro-text)' }}>
          <span className="material-symbols-outlined" style={{ fontSize: 15, color }}>{icon}</span>
          {label}
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ fontSize: 12, color: 'var(--pro-muted)' }}>{value.toLocaleString()}</span>
          <span style={{ fontSize: 12, fontWeight: 700, color, minWidth: 32, textAlign: 'right' }}>{pct}%</span>
        </div>
      </div>
      <div style={{ height: 5, borderRadius: 4, background: 'var(--pro-surface3)', overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: 4, transition: 'width 0.5s ease' }} />
      </div>
    </div>
  )
}
