/**
 * Dashboard — Painel de Controle with stats, lead insights, and intelligence logs.
 */
import { useState, useEffect } from 'react'
import { Users, Mail, Phone, Zap, Calendar, CalendarDays, CalendarRange } from 'lucide-react'
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

  return (
    <div className="content-wrapper" style={{ display: 'flex', flexDirection: 'column', minHeight: 'calc(100vh - 60px)' }}>
      {/* Stat Grid Row 1 — 4 cols */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 14 }}>
        <div className="stat-card">
          <div className="sc-label">
            Total de Leads
            <Users size={18} strokeWidth={1.5} style={{ opacity: 0.5 }} />
          </div>
          <div className="sc-val brand">{leadStats?.total?.toLocaleString() ?? '0'}</div>
          <div className="sc-delta" style={{ color: 'var(--pro-success)' }}>↑ 12% este mês</div>
        </div>
        <div className="stat-card">
          <div className="sc-label">
            Com Email
            <Mail size={18} strokeWidth={1.5} style={{ opacity: 0.5 }} />
          </div>
          <div className="sc-val">{leadStats?.with_email?.toLocaleString() ?? '0'}</div>
        </div>
        <div className="stat-card">
          <div className="sc-label">
            Com Telefone
            <Phone size={18} strokeWidth={1.5} style={{ opacity: 0.5 }} />
          </div>
          <div className="sc-val">{leadStats?.with_phone?.toLocaleString() ?? '0'}</div>
        </div>
        <div className="stat-card">
          <div className="sc-label">
            Processos Ativos
            <Zap size={18} strokeWidth={1.5} style={{ opacity: 0.5 }} />
          </div>
          <div className="sc-val" style={{ color: 'var(--pro-warning)' }}>{activeTasks.length}</div>
        </div>
      </div>

      {/* Stat Grid Row 2 — 3 cols (GSheets) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, marginBottom: 22 }}>
        <div className="stat-card">
          <div className="sc-label">
            Enviados Hoje
            <Calendar size={18} strokeWidth={1.5} style={{ opacity: 0.5 }} />
          </div>
          <div className="sc-val">{sendStats?.today ?? 0}</div>
        </div>
        <div className="stat-card">
          <div className="sc-label">
            Enviados Esta Semana
            <CalendarDays size={18} strokeWidth={1.5} style={{ opacity: 0.5 }} />
          </div>
          <div className="sc-val">{sendStats?.week ?? 0}</div>
        </div>
        <div className="stat-card">
          <div className="sc-label">
            Enviados Este Mês
            <CalendarRange size={18} strokeWidth={1.5} style={{ opacity: 0.5 }} />
          </div>
          <div className="sc-val">{sendStats?.month ?? 0}</div>
        </div>
      </div>

      {/* Bottom Grid — 2 cols with better fill */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, flex: 1, minHeight: 0 }}>
        {/* Left: Visão de Leads */}
        <div className="pro-card pro-card-accent" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--pro-text)', marginBottom: 6 }}>Visão de Leads</div>
          <div style={{ fontSize: 15, color: 'var(--pro-muted)', marginBottom: 24 }}>Qualidade do banco de dados</div>

          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <ProgressRow label="Com Telefone" dotColor="#16a34a" pct={leadStats ? Math.round((leadStats.with_phone / (leadStats.total || 1)) * 100) : 0} />
            <ProgressRow label="Com Email" dotColor="#2563eb" pct={leadStats ? Math.round((leadStats.with_email / (leadStats.total || 1)) * 100) : 0} gradientColors="linear-gradient(90deg,#2563eb,#60a5fa)" />
            <ProgressRow label="Com Website" dotColor="#7c3aed" pct={leadStats ? Math.round((leadStats.with_website / (leadStats.total || 1)) * 100) : 0} gradientColors="linear-gradient(90deg,#7c3aed,#a78bfa)" />
            <ProgressRow label="Sem Telefone" dotColor="#dc2626" pct={leadStats ? Math.round((leadStats.without_phone / (leadStats.total || 1)) * 100) : 0} gradientColors="linear-gradient(90deg,#dc2626,#f87171)" last />
          </div>
        </div>

        {/* Right: Terminal Logs */}
        <div className="pro-terminal" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          <div className="term-head">
            <div className="term-dots">
              <div className="term-dot" style={{ background: '#dc2626' }} />
              <div className="term-dot" style={{ background: '#d97706' }} />
              <div className="term-dot" style={{ background: '#16a34a' }} />
            </div>
            <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--pro-text)', letterSpacing: '0.1em' }}>LOGS DE INTELIGÊNCIA</span>
            <div className="live-dot" style={{ marginLeft: 'auto' }} />
          </div>

          <div style={{ flex: 1, overflow: 'auto', minHeight: 140 }} className="custom-scrollbar">
            {tasks.length > 0 ? (
              tasks.flatMap(t => t.logs || []).reverse().slice(0, 20).map((log, i) => (
                <div key={i} className="term-line">
                  — [{log.level === 'error' ? 'FALHA' : log.level === 'success' ? <span className="hl">SUCESSO</span> : 'INFO'}] {log.message}
                </div>
              ))
            ) : (
              <>
                <div className="term-line">— [SISTEMA] Aguardando tarefas...</div>
                <div className="term-line">— [INFO] <span className="hl">Backend conectado</span></div>
                <div className="term-line">— [INFO] {activeTasks.length} processos em fila</div>
              </>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 10, paddingTop: 10, borderTop: '0.5px solid var(--pro-border)' }}>
            <span style={{ color: 'rgba(232,89,60,0.7)' }}>›</span>
            <input
              type="text"
              style={{
                flex: 1, background: 'transparent', border: 'none', padding: 0,
                fontSize: 15, color: 'var(--pro-muted)', fontFamily: 'monospace',
                outline: 'none',
              }}
              placeholder="Executar comando..."
            />
            <div className="term-cursor" />
          </div>
        </div>
      </div>
    </div>
  )
}

/* ── Sub-Components ───────────────────────────────────────── */

function ProgressRow({ label, dotColor, pct, gradientColors, last }) {
  return (
    <div style={{ marginBottom: last ? 0 : 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--pro-text)', display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 10, height: 10, borderRadius: '50%', background: dotColor, flexShrink: 0 }} />
          {label}
        </div>
        <div style={{ fontSize: 16, color: 'var(--pro-muted)', fontWeight: 700 }}>{pct}%</div>
      </div>
      <div className="prog-bar" style={{ height: 6 }}>
        <div className="prog-fill" style={{ width: `${pct}%`, ...(gradientColors ? { background: gradientColors } : {}) }} />
      </div>
    </div>
  )
}
