/**
 * Leads Management Page — tabbed layout with Google Sheets integration
 */
import { useState, useEffect } from 'react'
import { leadsService, gsheetsService } from '../services/supabase'
import toast from 'react-hot-toast'

export default function LeadsPage() {
  const [activeTab, setActiveTab] = useState('leads')

  return (
    <div className="content-wrapper">
      {/* Tabs */}
      <div className="pro-tabs">
        {[
          { id: 'leads', label: 'Leads' },
          { id: 'gsheets', label: 'Google Sheets' },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`pro-tab ${activeTab === tab.id ? 'active' : ''}`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'leads' && <LeadsTab />}
      {activeTab === 'gsheets' && <GSheetsTab />}
    </div>
  )
}

/* ── LEADS TAB ──────────────────────────────────────────────── */

function LeadsTab() {
  const [leads, setLeads] = useState([])
  const [stats, setStats] = useState(null)
  const [conjuntos, setConjuntos] = useState([])
  const [cidades, setCidades] = useState([])

  const [selectedConjunto, setSelectedConjunto] = useState('')
  const [selectedCidade, setSelectedCidade] = useState('')
  const [searchTerm, setSearchTerm] = useState('')

  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [limit] = useState(50)

  const [loading, setLoading] = useState(false)
  const [selectedLeads, setSelectedLeads] = useState(new Set())
  const [editingLead, setEditingLead] = useState(null)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showSendModal, setShowSendModal] = useState(false)

  useEffect(() => { loadStats(); loadConjuntos(); loadLeads() }, [])
  useEffect(() => { loadLeads() }, [selectedConjunto, selectedCidade, searchTerm, page])
  useEffect(() => {
    if (selectedConjunto) loadCidades(selectedConjunto)
    else { setCidades([]); setSelectedCidade('') }
  }, [selectedConjunto])

  const loadStats = async () => {
    try { setStats(await leadsService.getStats()) }
    catch (e) { console.error(e) }
  }

  const loadConjuntos = async () => {
    try { setConjuntos(await leadsService.getConjuntos() || []) }
    catch (e) { console.error(e) }
  }

  const loadCidades = async (conjunto) => {
    try { setCidades(await leadsService.getCidades(conjunto) || []) }
    catch (e) { console.error(e) }
  }

  const loadLeads = async () => {
    setLoading(true)
    try {
      const { leads: data, total: count } = await leadsService.getLeads({
        limit, offset: (page - 1) * limit,
        conjunto: selectedConjunto || undefined,
        cidade: selectedCidade || undefined,
        search: searchTerm || undefined,
      })
      setLeads(data || [])
      setTotal(count || 0)
    } catch (e) {
      console.error(e)
      toast.error('Erro ao carregar leads')
      setLeads([]); setTotal(0)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Excluir este lead?')) return
    try {
      await leadsService.deleteLead(id)
      toast.success('Lead excluído')
      loadLeads(); loadStats()
    } catch (e) { toast.error('Erro ao excluir') }
  }

  const handleBulkDelete = async () => {
    if (!selectedLeads.size || !confirm(`Excluir ${selectedLeads.size} leads?`)) return
    try {
      await leadsService.deleteLeads([...selectedLeads])
      setSelectedLeads(new Set())
      toast.success(`${selectedLeads.size} leads excluídos`)
      loadLeads(); loadStats()
    } catch (e) { toast.error('Erro ao excluir') }
  }

  const handleSaveEdit = async () => {
    try {
      await leadsService.updateLead(editingLead.id, {
        nome: editingLead.nome, telefone: editingLead.telefone,
        website: editingLead.website, email: editingLead.email,
        endereco: editingLead.endereco, cidade: editingLead.cidade,
      })
      setShowEditModal(false); setEditingLead(null)
      toast.success('Lead atualizado')
      loadLeads()
    } catch (e) { toast.error('Erro ao atualizar') }
  }

  const handleExport = async () => {
    try {
      const data = await leadsService.exportLeads({
        conjunto: selectedConjunto || undefined,
        cidade: selectedCidade || undefined,
        search: searchTerm || undefined,
      })
      downloadCSV(convertToCSV(data), `leads-${Date.now()}.csv`)
      toast.success(`${data.length} leads exportados`)
    } catch (e) { toast.error('Erro ao exportar') }
  }

  const convertToCSV = (data) => {
    if (!data?.length) return ''
    const headers = ['ID', 'Nome', 'Telefone', 'Email', 'Website', 'Endereço', 'Cidade', 'Conjunto', 'URL', 'Data']
    const rows = data.map(l => [
      l.id, l.nome, l.telefone || '', l.email || '', l.website || '',
      l.endereco || '', l.cidade || '', l.conjunto_de_locais || '', l.url || '',
      new Date(l.created_at).toLocaleString('pt-BR'),
    ])
    return [headers, ...rows].map(r => r.map(c => `"${c}"`).join(';')).join('\n')
  }

  const downloadCSV = (csv, filename) => {
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = filename
    link.click()
  }

  const toggleSelectAll = () => {
    setSelectedLeads(selectedLeads.size === leads.length ? new Set() : new Set(leads.map(l => l.id)))
  }

  const toggleSelect = (id) => {
    const s = new Set(selectedLeads)
    s.has(id) ? s.delete(id) : s.add(id)
    setSelectedLeads(s)
  }

  const totalPages = Math.ceil(total / limit)

  return (
    <div className="space-y-6">
      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <StatCard label="Total" value={stats.total} icon="groups" />
          <StatCard label="Com Telefone" value={stats.with_phone} icon="phone" color="text-primary" />
          <StatCard label="Com Email" value={stats.with_email} icon="email" color="text-secondary" />
          <StatCard label="Com Website" value={stats.with_website} icon="language" color="text-tertiary" />
          <StatCard label="Sem Telefone" value={stats.without_phone} icon="phone_disabled" color="text-error" />
          <StatCard label="Sem Website" value={stats.without_website} icon="link_off" color="text-on-surface-variant" />
        </div>
      )}

      {/* Filters */}
      <div className="glass-card p-6 rounded-lg space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="md:col-span-2">
            <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Buscar</label>
            <input type="text" value={searchTerm}
              onChange={(e) => { setSearchTerm(e.target.value); setPage(1) }}
              placeholder="Nome, telefone, email ou website..." className="w-full" />
          </div>
          <div>
            <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Conjunto</label>
            <select value={selectedConjunto}
              onChange={(e) => { setSelectedConjunto(e.target.value); setPage(1) }} className="w-full">
              <option value="">Todos</option>
              {conjuntos.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Cidade</label>
            <select value={selectedCidade}
              onChange={(e) => { setSelectedCidade(e.target.value); setPage(1) }}
              className="w-full" disabled={!selectedConjunto}>
              <option value="">Todas</option>
              {cidades.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-outline-variant/10">
          <div className="flex items-center gap-2 flex-wrap">
            {selectedLeads.size > 0 && (
              <>
                <span className="text-sm text-on-surface-variant">{selectedLeads.size} selecionado(s)</span>
                <button onClick={() => setShowSendModal(true)} className="btn-primary">
                  <span className="material-symbols-outlined text-sm">send</span>
                  Enviar para Planilhas
                </button>
                <button onClick={handleBulkDelete} className="btn-ghost text-error border-error hover:bg-error/10">
                  <span className="material-symbols-outlined text-sm">delete</span>
                  Excluir
                </button>
              </>
            )}
          </div>
          <button onClick={handleExport} className="btn-primary">
            <span className="material-symbols-outlined text-lg">download</span>
            Exportar CSV
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="glass-card rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-12 text-center">
            <div className="inline-block w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
            <p className="mt-4 text-on-surface-variant">Carregando leads...</p>
          </div>
        ) : leads.length === 0 ? (
          <div className="p-12 text-center">
            <span className="material-symbols-outlined text-6xl text-on-surface-variant opacity-30">search_off</span>
            <p className="mt-4 text-on-surface-variant">Nenhum lead encontrado</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-surface-container-high border-b border-outline-variant/10">
                  <tr>
                    <th className="p-4 text-left">
                      <input type="checkbox"
                        checked={selectedLeads.size === leads.length && leads.length > 0}
                        onChange={toggleSelectAll} className="w-4 h-4" />
                    </th>
                    {['Nome', 'Telefone', 'Email', 'Website', 'Cidade', 'Conjunto', 'Ações'].map(h => (
                      <th key={h} className="p-4 text-left text-xs font-bold uppercase tracking-wider">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {leads.map((lead) => (
                    <tr key={lead.id} className="border-b border-outline-variant/5 hover:bg-surface-container-low/30 transition-colors">
                      <td className="p-4">
                        <input type="checkbox" checked={selectedLeads.has(lead.id)}
                          onChange={() => toggleSelect(lead.id)} className="w-4 h-4" />
                      </td>
                      <td className="p-4">
                        <div className="font-semibold">{lead.nome}</div>
                        {lead.endereco && <div className="text-xs text-on-surface-variant mt-1">{lead.endereco}</div>}
                      </td>
                      <td className="p-4">
                        {lead.telefone && lead.telefone !== 'Sem Telefone' ? (
                          <a href={`tel:${lead.telefone}`} className="text-primary hover:underline flex items-center gap-1">
                            <span className="material-symbols-outlined text-sm">phone</span>
                            {lead.telefone}
                          </a>
                        ) : <span className="text-on-surface-variant text-sm">—</span>}
                      </td>
                      <td className="p-4">
                        {lead.email ? (
                          <a href={`mailto:${lead.email}`} className="text-primary hover:underline flex items-center gap-1">
                            <span className="material-symbols-outlined text-sm">email</span>
                            <span className="truncate max-w-[160px] block">{lead.email}</span>
                          </a>
                        ) : <span className="text-on-surface-variant text-sm">—</span>}
                      </td>
                      <td className="p-4">
                        {lead.website && lead.website !== 'Sem Website' ? (
                          <a href={lead.website} target="_blank" rel="noopener noreferrer" className="text-secondary hover:underline flex items-center gap-1">
                            <span className="material-symbols-outlined text-sm">language</span>
                            <span className="truncate max-w-[160px] block">{lead.website}</span>
                          </a>
                        ) : <span className="text-on-surface-variant text-sm">—</span>}
                      </td>
                      <td className="p-4 text-sm">{lead.cidade || '—'}</td>
                      <td className="p-4">
                        <span className="px-2 py-1 rounded-full bg-primary/20 text-primary text-xs font-semibold">
                          {lead.conjunto_de_locais || 'N/A'}
                        </span>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center justify-end gap-1">
                          {lead.url && (
                            <a href={lead.url} target="_blank" rel="noopener noreferrer"
                              className="p-2 rounded-lg hover:bg-surface-container-highest transition-all" title="Ver no Maps">
                              <span className="material-symbols-outlined text-sm text-on-surface-variant">map</span>
                            </a>
                          )}
                          <button onClick={() => { setEditingLead({ ...lead }); setShowEditModal(true) }}
                            className="p-2 rounded-lg hover:bg-surface-container-highest transition-all">
                            <span className="material-symbols-outlined text-sm text-on-surface-variant">edit</span>
                          </button>
                          <button onClick={() => handleDelete(lead.id)}
                            className="p-2 rounded-lg hover:bg-surface-container-highest transition-all">
                            <span className="material-symbols-outlined text-sm text-error">delete</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {totalPages > 1 && (
              <div className="flex items-center justify-between p-4 border-t border-outline-variant/10">
                <div className="text-sm text-on-surface-variant">
                  Mostrando {(page - 1) * limit + 1}–{Math.min(page * limit, total)} de {total} leads
                </div>
                <div className="flex items-center gap-2">
                  <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                    className="p-2 rounded-lg hover:bg-surface-container-highest disabled:opacity-30 disabled:cursor-not-allowed">
                    <span className="material-symbols-outlined">chevron_left</span>
                  </button>
                  <span className="text-sm font-semibold px-4">Página {page} de {totalPages}</span>
                  <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}
                    className="p-2 rounded-lg hover:bg-surface-container-highest disabled:opacity-30 disabled:cursor-not-allowed">
                    <span className="material-symbols-outlined">chevron_right</span>
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {showEditModal && editingLead && (
        <EditLeadModal lead={editingLead} onSave={handleSaveEdit}
          onClose={() => { setShowEditModal(false); setEditingLead(null) }}
          onChange={setEditingLead} />
      )}

      {showSendModal && (
        <SendToSheetsModal
          leadIds={[...selectedLeads]}
          onClose={() => setShowSendModal(false)}
          onSent={() => { setShowSendModal(false); setSelectedLeads(new Set()) }}
        />
      )}
    </div>
  )
}

/* ── GSHEETS TAB ────────────────────────────────────────────── */

function GSheetsTab() {
  const [webhooks, setWebhooks] = useState([])
  const [history, setHistory] = useState([])
  const [sendStats, setSendStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [controlWebhook, setControlWebhook] = useState(null)

  useEffect(() => { loadAll() }, [])

  const loadAll = async () => {
    setLoading(true)
    try {
      const [wh, hist, stats] = await Promise.all([
        gsheetsService.getWebhooks(),
        gsheetsService.getSendHistory({ limit: 20 }),
        gsheetsService.getSendStats(),
      ])
      setWebhooks(wh)
      setHistory(hist)
      setSendStats(stats)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Excluir esta planilha?')) return
    try {
      await gsheetsService.deleteWebhook(id)
      toast.success('Planilha removida')
      loadAll()
    } catch (e) { toast.error('Erro ao remover') }
  }

  return (
    <div className="space-y-6">
      {/* Totals from Supabase send history */}
      {sendStats && (
        <div className="grid grid-cols-3 gap-4">
          <StatCard label="Enviados Hoje" value={sendStats.today} icon="today" color="text-primary" />
          <StatCard label="Esta Semana" value={sendStats.week} icon="date_range" color="text-secondary" />
          <StatCard label="Este Mês" value={sendStats.month} icon="calendar_month" color="text-tertiary" />
        </div>
      )}

      {/* Webhooks List */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-lg">Planilhas Cadastradas</h3>
          <button onClick={() => setShowAddModal(true)} className="btn-primary">
            <span className="material-symbols-outlined text-lg">add</span>
            Adicionar Planilha
          </button>
        </div>

        {loading ? (
          <div className="glass-card rounded-lg p-8 text-center">
            <div className="inline-block w-6 h-6 border-4 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : webhooks.length === 0 ? (
          <div className="glass-card rounded-lg p-12 text-center">
            <span className="material-symbols-outlined text-6xl text-on-surface-variant opacity-30">table_chart</span>
            <p className="mt-4 text-on-surface-variant">Nenhuma planilha cadastrada</p>
            <p className="text-sm text-on-surface-variant opacity-60 mt-1">
              Adicione uma planilha Google Sheets com webhook para enviar leads
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {webhooks.map(wh => (
              <WebhookCard
                key={wh.id}
                webhook={wh}
                onManage={() => setControlWebhook(wh)}
                onDelete={() => handleDelete(wh.id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Send History */}
      {history.length > 0 && (
        <div className="glass-card rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-outline-variant/10">
            <h3 className="font-bold text-lg">Histórico de Envios</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-surface-container-high border-b border-outline-variant/10">
                <tr>
                  {['Data', 'Planilha', 'Leads', 'Status'].map(h => (
                    <th key={h} className="p-4 text-left text-xs font-bold uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {history.map(h => (
                  <tr key={h.id} className="border-b border-outline-variant/5 hover:bg-surface-container-low/30 transition-colors">
                    <td className="p-4 text-sm">{new Date(h.sent_at).toLocaleString('pt-BR')}</td>
                    <td className="p-4 text-sm">{h.webhook_name || h.gsheets_webhooks?.name || '—'}</td>
                    <td className="p-4 text-sm font-semibold">{h.leads_sent}</td>
                    <td className="p-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                        h.status === 'success' ? 'bg-primary/20 text-primary' : 'bg-error/20 text-error'
                      }`}>
                        {h.status === 'success' ? 'Sucesso' : 'Erro'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {showAddModal && (
        <AddWebhookModal onClose={() => setShowAddModal(false)} onAdded={loadAll} />
      )}

      {controlWebhook && (
        <WebhookControlModal
          webhook={controlWebhook}
          onClose={() => setControlWebhook(null)}
        />
      )}
    </div>
  )
}

/* ── WEBHOOK CARD (live stats from AppScript) ───────────────── */

function WebhookCard({ webhook, onManage, onDelete }) {
  const [stats, setStats] = useState(null)
  const [loadingStats, setLoadingStats] = useState(true)
  const [triggering, setTriggering] = useState(false)
  const [togglingSchedule, setTogglingSchedule] = useState(false)

  const fetchStats = async () => {
    setLoadingStats(true)
    try {
      const res = await fetch(webhook.webhook_url + '?action=stats')
      const data = await res.json()
      setStats(data)
    } catch {
      setStats(null)
    } finally {
      setLoadingStats(false)
    }
  }

  useEffect(() => { fetchStats() }, [webhook.webhook_url])

  // Usa GET com ?payload= para evitar CORS preflight (Apps Script não suporta OPTIONS)
  const apiPost = async (payload) => {
    const url = webhook.webhook_url + '?payload=' + encodeURIComponent(JSON.stringify(payload))
    const res = await fetch(url)
    return res.json()
  }

  const handleToggleSchedule = async () => {
    if (!stats) return
    const next = !stats.schedule_active
    if (next && !stats.subject) {
      toast.error('Configure o assunto do rascunho antes de ativar o robô')
      onManage()
      return
    }
    setTogglingSchedule(true)
    try {
      const res = await apiPost({ action: next ? 'schedule' : 'stop', active: next })
      if (res.success) {
        toast.success(next ? 'Robô ativado!' : 'Robô parado!')
        fetchStats()
      } else {
        toast.error(res.error || 'Erro')
      }
    } catch { toast.error('Erro de conexão') }
    finally { setTogglingSchedule(false) }
  }

  const handleTrigger = async () => {
    if (!confirm(`Disparar um lote de emails agora para "${webhook.name}"?`)) return
    setTriggering(true)
    try {
      const res = await apiPost({ action: 'trigger_send' })
      if (res.success) {
        toast.success(`${res.sent} email(s) enviado(s)!`)
        fetchStats()
      } else {
        toast.error(res.error || 'Erro ao disparar')
      }
    } catch { toast.error('Erro de conexão') }
    finally { setTriggering(false) }
  }

  const scheduleActive = stats?.schedule_active
  const dailyPct = stats?.daily_limit > 0
    ? Math.min(100, Math.round((stats.daily_sent / stats.daily_limit) * 100))
    : 0

  return (
    <div className="glass-card rounded-xl overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-outline-variant/10 flex items-center gap-3">
        <span className="material-symbols-outlined text-primary" style={{ fontSize: 20 }}>table_chart</span>
        <div className="flex-1 min-w-0">
          <div className="font-bold">{webhook.name}</div>
          {webhook.description && (
            <div className="text-xs text-on-surface-variant mt-0.5">{webhook.description}</div>
          )}
        </div>
        {/* Robot status badge */}
        <span className={`px-2.5 py-1 rounded-full text-xs font-bold flex items-center gap-1.5 ${
          scheduleActive
            ? 'bg-primary/15 text-primary'
            : 'bg-surface-container-high text-on-surface-variant'
        }`}>
          <span className={`inline-block w-1.5 h-1.5 rounded-full ${scheduleActive ? 'bg-primary animate-pulse' : 'bg-on-surface-variant opacity-40'}`} />
          {scheduleActive ? 'ATIVO' : 'INATIVO'}
        </span>
      </div>

      {/* Stats body */}
      <div className="px-5 py-4">
        {loadingStats ? (
          <div className="flex items-center gap-2 text-sm text-on-surface-variant py-2">
            <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            Carregando stats...
          </div>
        ) : stats ? (
          <>
            {/* Main stats row */}
            <div className="grid grid-cols-4 gap-3 mb-4">
              {[
                { label: 'Total', value: stats.total ?? '—', color: '' },
                { label: 'Enviados', value: stats.sent ?? '—', color: 'text-primary' },
                { label: 'Pendentes', value: stats.pending ?? '—', color: 'text-secondary' },
                { label: 'Erros', value: stats.errors ?? '—', color: stats.errors > 0 ? 'text-error' : '' },
              ].map(s => (
                <div key={s.label} className="bg-surface-container rounded-lg p-3 text-center">
                  <div className={`text-xl font-bold ${s.color}`}>{s.value}</div>
                  <div className="text-xs text-on-surface-variant mt-1">{s.label}</div>
                </div>
              ))}
            </div>

            {/* Secondary row */}
            <div className="grid grid-cols-2 gap-3 mb-4">
              <div className="bg-surface-container rounded-lg p-3">
                <div className="text-xs text-on-surface-variant mb-1">Cota Gmail Hoje</div>
                <div className={`text-lg font-bold ${(stats.quota_gmail ?? 100) > 85 ? 'text-primary' : 'text-error'}`}>
                  {stats.quota_gmail ?? '—'}%
                </div>
              </div>
              <div className="bg-surface-container rounded-lg p-3">
                <div className="text-xs text-on-surface-variant mb-1">Enviados hoje (robô)</div>
                <div className="text-lg font-bold">{stats.daily_sent ?? 0} <span className="text-sm font-normal text-on-surface-variant">/ {stats.daily_limit ?? webhook.daily_limit}</span></div>
              </div>
            </div>

            {/* Daily progress bar */}
            {(stats.daily_limit ?? 0) > 0 && (
              <div className="mb-1">
                <div className="flex justify-between text-xs text-on-surface-variant mb-1.5">
                  <span>Progresso diário</span>
                  <span>{dailyPct}% · {stats.daily_remaining ?? 0} restantes</span>
                </div>
                <div className="h-1.5 bg-surface-container-high rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: dailyPct + '%',
                      background: dailyPct > 90 ? '#E8593C' : 'linear-gradient(90deg, #0055ff, #00aaff)',
                    }}
                  />
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="text-sm text-error flex items-center gap-2 py-2">
            <span className="material-symbols-outlined text-base">error</span>
            Não foi possível conectar à planilha
          </div>
        )}
      </div>

      {/* Actions footer */}
      <div className="px-5 pb-4 flex items-center gap-2 flex-wrap">
        <button
          onClick={handleToggleSchedule}
          disabled={togglingSchedule || loadingStats}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all disabled:opacity-50 ${
            scheduleActive
              ? 'bg-error/15 text-error hover:bg-error/25'
              : 'bg-primary/15 text-primary hover:bg-primary/25'
          }`}
        >
          {togglingSchedule
            ? <span className="inline-block w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
            : <span className="material-symbols-outlined" style={{ fontSize: 14 }}>{scheduleActive ? 'stop_circle' : 'play_circle'}</span>
          }
          {scheduleActive ? 'Parar robô' : 'Ativar robô'}
        </button>

        <button
          onClick={handleTrigger}
          disabled={triggering || loadingStats}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-surface-container-high hover:bg-surface-container-highest text-on-surface transition-all disabled:opacity-50"
        >
          {triggering
            ? <span className="inline-block w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
            : <span className="material-symbols-outlined" style={{ fontSize: 14 }}>rocket_launch</span>
          }
          Disparar agora
        </button>

        <button
          onClick={fetchStats}
          disabled={loadingStats}
          className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs text-on-surface-variant hover:bg-surface-container-high transition-all disabled:opacity-50"
          title="Atualizar"
        >
          <span className="material-symbols-outlined" style={{ fontSize: 14 }}>refresh</span>
        </button>

        <div className="ml-auto flex items-center gap-1">
          <button
            onClick={onManage}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-surface-container-high hover:bg-surface-container-highest text-on-surface transition-all"
          >
            <span className="material-symbols-outlined" style={{ fontSize: 14 }}>settings</span>
            Configurar
          </button>
          <button
            onClick={onDelete}
            className="p-1.5 rounded-lg text-error hover:bg-error/10 transition-all"
            title="Remover planilha"
          >
            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>delete</span>
          </button>
        </div>
      </div>
    </div>
  )
}

/* ── MODALS ─────────────────────────────────────────────────── */

function SendToSheetsModal({ leadIds, onClose, onSent }) {
  const [webhooks, setWebhooks] = useState([])
  const [selectedWebhooks, setSelectedWebhooks] = useState(new Set())
  const [distribution, setDistribution] = useState('all')
  const [sending, setSending] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    gsheetsService.getWebhooks()
      .then(wh => { setWebhooks(wh.filter(w => w.active)); setLoading(false) })
      .catch(e => { console.error(e); setLoading(false) })
  }, [])

  const toggleWebhook = (id) => {
    const s = new Set(selectedWebhooks)
    s.has(id) ? s.delete(id) : s.add(id)
    setSelectedWebhooks(s)
  }

  const handleSend = async () => {
    if (!selectedWebhooks.size) { toast.error('Selecione ao menos uma planilha'); return }
    setSending(true)
    try {
      const leads = await leadsService.getLeadsByIds(leadIds)
      const activeWebhooks = webhooks.filter(w => selectedWebhooks.has(w.id))

      let assignments = []
      if (distribution === 'all') {
        assignments = activeWebhooks.map(w => ({ webhook: w, leads }))
      } else if (distribution === 'equal') {
        const chunkSize = Math.ceil(leads.length / activeWebhooks.length)
        assignments = activeWebhooks.map((w, i) => ({
          webhook: w, leads: leads.slice(i * chunkSize, (i + 1) * chunkSize)
        }))
      } else if (distribution === 'daily_limit') {
        let remaining = [...leads]
        assignments = activeWebhooks.map(w => {
          const chunk = remaining.splice(0, w.daily_limit)
          return { webhook: w, leads: chunk }
        })
      }

      let totalSent = 0
      for (const { webhook, leads: batch } of assignments) {
        if (!batch.length) continue
        try {
          const payload = {
            leads: batch.map(l => ({
              EMPRESA: l.nome, EMAIL: l.email || '', TELEFONE: l.telefone || '',
              CIDADE: l.cidade || '', WEBSITE: l.website || '',
            })),
            source: 'prospectahub',
            sent_at: new Date().toISOString(),
          }
          const res = await fetch(webhook.webhook_url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
          })
          const status = res.ok ? 'success' : 'error'
          await gsheetsService.recordSend({
            webhook_id: webhook.id, webhook_name: webhook.name,
            leads_sent: batch.length, status,
          })
          if (res.ok) totalSent += batch.length
        } catch (e) {
          await gsheetsService.recordSend({
            webhook_id: webhook.id, webhook_name: webhook.name,
            leads_sent: 0, status: 'error', error_detail: e.message,
          })
        }
      }

      toast.success(`${totalSent} leads enviados para ${selectedWebhooks.size} planilha(s)`)
      onSent()
    } catch (e) {
      console.error(e)
      toast.error('Erro ao enviar leads')
    } finally {
      setSending(false)
    }
  }

  const getPreview = () => {
    const count = selectedWebhooks.size
    if (!count) return 'Selecione planilhas'
    if (distribution === 'all') return `${leadIds.length} leads → cada planilha`
    if (distribution === 'equal') return `~${Math.ceil(leadIds.length / count)} leads/planilha`
    if (distribution === 'daily_limit') {
      const total = webhooks.filter(w => selectedWebhooks.has(w.id)).reduce((s, w) => s + w.daily_limit, 0)
      return `Até ${Math.min(leadIds.length, total)} leads distribuídos`
    }
  }

  return (
    <Modal title="Enviar para Planilhas" onClose={onClose}>
      {loading ? (
        <div className="p-8 text-center">
          <div className="inline-block w-6 h-6 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      ) : webhooks.length === 0 ? (
        <div className="p-8 text-center text-on-surface-variant">
          Nenhuma planilha ativa. Cadastre uma na aba Google Sheets.
        </div>
      ) : (
        <div className="space-y-6">
          <div>
            <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-3">
              Planilhas de destino
            </label>
            <div className="space-y-2">
              {webhooks.map(w => (
                <label key={w.id} className="flex items-center gap-3 p-3 rounded-lg hover:bg-surface-container-low cursor-pointer">
                  <input type="checkbox" checked={selectedWebhooks.has(w.id)}
                    onChange={() => toggleWebhook(w.id)} className="w-4 h-4" />
                  <div className="flex-1">
                    <div className="font-medium">{w.name}</div>
                    {w.description && <div className="text-xs text-on-surface-variant">{w.description}</div>}
                  </div>
                  <span className="text-xs text-on-surface-variant">Limite: {w.daily_limit}/dia</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-3">
              Modo de distribuição
            </label>
            <div className="space-y-2">
              {[
                { id: 'all', label: 'Todos para cada planilha', desc: 'Duplica os leads em todas as planilhas selecionadas' },
                { id: 'equal', label: 'Distribuir igualmente', desc: 'Divide os leads entre as planilhas selecionadas' },
                { id: 'daily_limit', label: 'Respeitar limite diário', desc: 'Não ultrapassa o limite configurado por planilha' },
              ].map(opt => (
                <label key={opt.id} className="flex items-start gap-3 p-3 rounded-lg hover:bg-surface-container-low cursor-pointer">
                  <input type="radio" name="distribution" value={opt.id}
                    checked={distribution === opt.id} onChange={() => setDistribution(opt.id)} className="mt-0.5" />
                  <div>
                    <div className="font-medium text-sm">{opt.label}</div>
                    <div className="text-xs text-on-surface-variant">{opt.desc}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          <div className="bg-surface-container rounded-lg p-4 text-sm">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-base">info</span>
              <span><strong>{leadIds.length} leads</strong> selecionados — {getPreview()}</span>
            </div>
          </div>
        </div>
      )}

      <div className="flex items-center justify-end gap-4 pt-4 border-t border-outline-variant/10 mt-4">
        <button onClick={onClose} className="btn-ghost">Cancelar</button>
        <button onClick={handleSend} disabled={sending || !selectedWebhooks.size}
          className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed">
          {sending ? (
            <><span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />Enviando...</>
          ) : (
            <><span className="material-symbols-outlined text-lg">send</span>Enviar</>
          )}
        </button>
      </div>
    </Modal>
  )
}

function AddWebhookModal({ onClose, onAdded }) {
  const [form, setForm] = useState({ name: '', webhook_url: '', description: '', daily_limit: 80 })
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    if (!form.name || !form.webhook_url) { toast.error('Nome e URL são obrigatórios'); return }
    setSaving(true)
    try {
      await gsheetsService.createWebhook(form)
      toast.success('Planilha adicionada!')
      onAdded(); onClose()
    } catch (e) { toast.error('Erro ao salvar'); setSaving(false) }
  }

  return (
    <Modal title="Adicionar Planilha" onClose={onClose}>
      <div className="space-y-4">
        <div>
          <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Nome *</label>
          <input type="text" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })}
            placeholder="Ex: Planilha Prospecção SP" className="w-full" />
        </div>
        <div>
          <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">URL do Webhook *</label>
          <input type="url" value={form.webhook_url} onChange={e => setForm({ ...form, webhook_url: e.target.value })}
            placeholder="https://script.google.com/macros/s/.../exec" className="w-full" />
        </div>
        <div>
          <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Descrição</label>
          <input type="text" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })}
            placeholder="Planilha para campanha X" className="w-full" />
        </div>
        <div>
          <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Limite diário</label>
          <input type="number" value={form.daily_limit} min={1}
            onChange={e => setForm({ ...form, daily_limit: parseInt(e.target.value) || 80 })} className="w-full" />
        </div>
      </div>

      <div className="flex items-center justify-end gap-4 pt-4 border-t border-outline-variant/10 mt-4">
        <button onClick={onClose} className="btn-ghost">Cancelar</button>
        <button onClick={handleSave} disabled={saving} className="btn-primary disabled:opacity-50">
          <span className="material-symbols-outlined text-lg">save</span>
          {saving ? 'Salvando...' : 'Salvar'}
        </button>
      </div>
    </Modal>
  )
}

function EditLeadModal({ lead, onSave, onClose, onChange }) {
  return (
    <Modal title="Editar Lead" onClose={onClose}>
      <div className="space-y-4">
        {[
          { key: 'nome', label: 'Nome', type: 'text' },
          { key: 'telefone', label: 'Telefone', type: 'text' },
          { key: 'website', label: 'Website', type: 'text' },
          { key: 'email', label: 'Email', type: 'email' },
          { key: 'endereco', label: 'Endereço', type: 'text' },
          { key: 'cidade', label: 'Cidade', type: 'text' },
        ].map(({ key, label, type }) => (
          <div key={key}>
            <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">{label}</label>
            <input type={type} value={lead[key] || ''}
              onChange={(e) => onChange({ ...lead, [key]: e.target.value })} className="w-full" />
          </div>
        ))}
      </div>
      <div className="flex items-center justify-end gap-4 pt-4 border-t border-outline-variant/10 mt-4">
        <button onClick={onClose} className="btn-ghost">Cancelar</button>
        <button onClick={onSave} className="btn-primary">
          <span className="material-symbols-outlined text-lg">save</span>Salvar
        </button>
      </div>
    </Modal>
  )
}

function Modal({ title, onClose, children }) {
  return (
    <div className="modal-overlay animate-fade-in" onClick={onClose}>
      <div className="modal-container animate-scale-in" style={{ maxWidth: 640, maxHeight: '85vh', overflow: 'hidden' }}
        onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">{title}</div>
          <button onClick={onClose} className="btn-icon">
            <span className="material-symbols-outlined text-on-surface-variant" style={{ fontSize: 18 }}>close</span>
          </button>
        </div>
        <div className="modal-body" style={{ overflowY: 'auto', maxHeight: 'calc(85vh - 160px)' }}>{children}</div>
      </div>
    </div>
  )
}

/* ── WEBHOOK CONTROL MODAL ──────────────────────────────────── */

function WebhookControlModal({ webhook, onClose }) {
  const [stats, setStats] = useState(null)
  const [loadingData, setLoadingData] = useState(true)
  const [saving, setSaving] = useState(false)
  const [triggering, setTriggering] = useState(false)

  const [webhookUrl, setWebhookUrl] = useState(webhook.webhook_url)
  const [savingUrl, setSavingUrl] = useState(false)

  const [subject, setSubject] = useState('')
  const [dailyLimit, setDailyLimit] = useState(80)
  const [batchSize, setBatchSize] = useState(20)
  const [minHour, setMinHour] = useState(8)
  const [maxHour, setMaxHour] = useState(16)
  const [selectedDays, setSelectedDays] = useState([])

  const [reportEmail, setReportEmail] = useState('')
  const [savingReport, setSavingReport] = useState(false)

  const DAYS = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']

  useEffect(() => { loadData() }, [])

  const currentUrl = webhookUrl || webhook.webhook_url

  const handleSaveUrl = async () => {
    if (!webhookUrl.trim()) { toast.error('URL não pode ser vazia'); return }
    setSavingUrl(true)
    try {
      await gsheetsService.updateWebhook(webhook.id, { webhook_url: webhookUrl.trim() })
      toast.success('URL atualizada! Recarregando stats...')
      // reload data with new URL
      loadData()
    } catch { toast.error('Erro ao salvar URL') }
    finally { setSavingUrl(false) }
  }

  // Usa GET com ?payload= para evitar CORS preflight (Apps Script não suporta OPTIONS)
  const apiPost = async (payload) => {
    const url = currentUrl + '?payload=' + encodeURIComponent(JSON.stringify(payload))
    const res = await fetch(url)
    return res.json()
  }

  const loadData = async () => {
    setLoadingData(true)
    try {
      const [statsRes, settingsRes] = await Promise.all([
        fetch(currentUrl + '?action=stats').then(r => r.json()),
        fetch(currentUrl + '?action=settings').then(r => r.json()),
      ])
      const reportRes = await fetch(currentUrl + '?action=report_config').then(r => r.json()).catch(() => ({}))
      setStats(statsRes)
      if (settingsRes.success !== false) {
        setSubject(settingsRes.subject || '')
        setDailyLimit(settingsRes.daily_limit || 80)
        setBatchSize(settingsRes.hourly_batch_size || 20)
        setMinHour(settingsRes.min_hour || 8)
        setMaxHour(settingsRes.max_hour || 16)
        setSelectedDays(settingsRes.days || [])
      }
      if (reportRes.success !== false) {
        setReportEmail(reportRes.report_email || '')
      }
    } catch {
      toast.error('Erro ao conectar com a planilha. Verifique a URL do webhook.')
    } finally {
      setLoadingData(false)
    }
  }

  const handleConfigure = async () => {
    if (!subject.trim()) { toast.error('Defina o assunto do rascunho Gmail'); return }
    setSaving(true)
    try {
      const res = await apiPost({
        action: 'configure', subject,
        daily_limit: dailyLimit, hourly_batch_size: batchSize,
        min_hour: minHour, max_hour: maxHour,
      })
      if (res.success) { toast.success('Configurações salvas!'); loadData() }
      else toast.error(res.error || 'Erro ao salvar')
    } catch { toast.error('Erro de conexão') }
    finally { setSaving(false) }
  }

  const handleSchedule = async (active) => {
    if (active && selectedDays.length === 0) { toast.error('Selecione ao menos um dia'); return }
    if (active && !subject.trim()) { toast.error('Salve as configurações (assunto) antes de ativar'); return }
    setSaving(true)
    try {
      const res = await apiPost({ action: 'schedule', active, days: selectedDays, subject })
      if (res.success) { toast.success(active ? 'Agendamento ativado!' : 'Agendamento parado!'); loadData() }
      else toast.error(res.error || 'Erro')
    } catch { toast.error('Erro de conexão') }
    finally { setSaving(false) }
  }

  const handleTrigger = async () => {
    if (!subject.trim()) { toast.error('Configure o assunto primeiro'); return }
    if (!confirm(`Disparar até ${batchSize} emails agora para "${webhook.name}"?`)) return
    setTriggering(true)
    try {
      const res = await apiPost({ action: 'trigger_send', limit: batchSize })
      if (res.success) {
        toast.success(`${res.sent} email(s) enviado(s)! Pendentes: ${res.pending_after}`)
        loadData()
      } else toast.error(res.error || 'Erro ao disparar')
    } catch { toast.error('Erro de conexão') }
    finally { setTriggering(false) }
  }

  const handleStop = async () => {
    if (!confirm('Parar o agendamento automático desta planilha?')) return
    try {
      const res = await apiPost({ action: 'stop' })
      if (res.success) { toast.success('Agendamento parado'); loadData() }
    } catch { toast.error('Erro') }
  }

  const handleClear = async () => {
    if (!confirm(`Limpar TODOS os leads da planilha "${webhook.name}"?\n\nEsta ação não pode ser desfeita.`)) return
    try {
      const res = await apiPost({ action: 'clear' })
      if (res.success) { toast.success('Lista limpa!'); loadData() }
    } catch { toast.error('Erro') }
  }

  const configureReport = async (enabled) => {
    if (enabled && !reportEmail.trim()) { toast.error('Informe o email para receber o relatório'); return }
    setSavingReport(true)
    try {
      const res = await apiPost({
        action: 'configure_report',
        recipient_email: reportEmail,
        enabled,
      })
      if (res.success) {
        toast.success(enabled ? 'Relatório diário ativado!' : 'Relatório diário desativado')
      } else {
        toast.error(res.error || 'Erro ao configurar relatório')
      }
    } catch { toast.error('Erro ao conectar com a planilha') }
    finally { setSavingReport(false) }
  }

  const toggleDay = (d) => {
    setSelectedDays(prev => prev.includes(d) ? prev.filter(x => x !== d) : [...prev, d])
  }

  return (
    <Modal title={`Gerenciar — ${webhook.name}`} onClose={onClose}>
      {/* URL do Webhook — editável para quando o AppScript gerar nova URL */}
      <div className="mb-5 p-4 rounded-lg" style={{ background: 'var(--pro-surface2)', border: '1px solid var(--pro-border)' }}>
        <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">
          URL do Webhook (AppScript)
        </label>
        <div className="flex gap-2">
          <input
            type="url"
            value={webhookUrl}
            onChange={e => setWebhookUrl(e.target.value)}
            placeholder="https://script.google.com/macros/s/.../exec"
            className="flex-1 text-xs"
          />
          <button
            onClick={handleSaveUrl}
            disabled={savingUrl || webhookUrl === webhook.webhook_url}
            className="btn-primary shrink-0 disabled:opacity-40 disabled:cursor-not-allowed"
            style={{ padding: '8px 14px', fontSize: 13 }}
          >
            {savingUrl
              ? <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              : <><span className="material-symbols-outlined text-base">save</span>Salvar</>
            }
          </button>
        </div>
        <p className="text-xs text-on-surface-variant mt-1.5 opacity-60">
          Cole aqui a nova URL sempre que reimplantar o AppScript no Google Sheets.
        </p>
      </div>

      {loadingData ? (
        <div className="p-8 text-center">
          <div className="inline-block w-6 h-6 border-4 border-primary border-t-transparent rounded-full animate-spin" />
          <p className="mt-3 text-on-surface-variant text-sm">Conectando à planilha...</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Stats em tempo real */}
          {stats && (
            <>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { label: 'Cota Gmail', value: stats.quota_gmail, color: stats.quota_gmail > 85 ? 'text-primary' : 'text-error' },
                  { label: 'Pendentes', value: stats.pending, color: 'text-secondary' },
                  { label: 'Enviados', value: stats.sent, color: 'text-primary' },
                ].map(s => (
                  <div key={s.label} className="bg-surface-container rounded-lg p-3 text-center">
                    <div className="text-xs text-on-surface-variant mb-1">{s.label}</div>
                    <div className={`text-2xl font-bold ${s.color}`}>{s.value ?? '—'}</div>
                  </div>
                ))}
              </div>

              <div className="bg-surface-container rounded-lg p-4 space-y-2">
                {[
                  { label: 'Total na planilha', value: stats.total },
                  { label: 'Enviados hoje (robô)', value: `${stats.daily_sent} / ${stats.daily_limit}` },
                  { label: 'Restam hoje', value: stats.daily_remaining, color: stats.daily_remaining > 0 ? 'text-primary' : 'text-error' },
                  { label: 'Erros', value: stats.errors, color: stats.errors > 0 ? 'text-error' : '' },
                ].map(row => (
                  <div key={row.label} className="flex justify-between text-sm">
                    <span className="text-on-surface-variant">{row.label}</span>
                    <span className={`font-semibold ${row.color || ''}`}>{row.value}</span>
                  </div>
                ))}
                <div className="flex justify-between text-sm pt-1 border-t border-outline-variant/10">
                  <span className="text-on-surface-variant">Agendamento</span>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                    stats.schedule_active ? 'bg-primary/20 text-primary' : 'bg-surface-container-high text-on-surface-variant'
                  }`}>{stats.schedule_active ? 'Ativo' : 'Inativo'}</span>
                </div>
              </div>

              <button onClick={loadData} className="btn-ghost w-full justify-center text-sm">
                <span className="material-symbols-outlined text-sm">refresh</span>
                Atualizar stats
              </button>
            </>
          )}

          {/* Configurações */}
          <div className="border-t border-outline-variant/10 pt-4">
            <h4 className="font-semibold mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-base text-primary">settings</span>
              Configurações de Envio
            </h4>
            <div className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">
                  Assunto do Rascunho (Gmail) *
                </label>
                <input type="text" value={subject} onChange={e => setSubject(e.target.value)}
                  placeholder="Ex: Proposta para {{EMPRESA}}" className="w-full" />
                <p className="text-xs text-on-surface-variant mt-1">
                  Crie um rascunho no Gmail com esse assunto. Use {`{{EMPRESA}}`}, {`{{EMAIL}}`}, {`{{CIDADE}}`} no corpo.
                </p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Limite diário (emails)</label>
                  <input type="number" value={dailyLimit} min={1} max={500}
                    onChange={e => setDailyLimit(parseInt(e.target.value) || 80)} className="w-full" />
                </div>
                <div>
                  <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Lote por hora</label>
                  <input type="number" value={batchSize} min={1} max={100}
                    onChange={e => setBatchSize(parseInt(e.target.value) || 20)} className="w-full" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Hora início</label>
                  <input type="number" value={minHour} min={0} max={23}
                    onChange={e => setMinHour(parseInt(e.target.value) || 8)} className="w-full" />
                </div>
                <div>
                  <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Hora fim</label>
                  <input type="number" value={maxHour} min={1} max={23}
                    onChange={e => setMaxHour(parseInt(e.target.value) || 16)} className="w-full" />
                </div>
              </div>
              <button onClick={handleConfigure} disabled={saving}
                className="btn-primary w-full justify-center disabled:opacity-50 disabled:cursor-not-allowed">
                {saving
                  ? <><span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />Salvando...</>
                  : <><span className="material-symbols-outlined text-lg">save</span>Salvar Configurações</>}
              </button>
            </div>
          </div>

          {/* Agendamento */}
          <div className="border-t border-outline-variant/10 pt-4">
            <h4 className="font-semibold mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-base text-primary">schedule</span>
              Agendamento Automático
            </h4>
            <div className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">
                  Dias de funcionamento
                </label>
                <div className="flex gap-1">
                  {DAYS.map((day, i) => (
                    <button key={i} onClick={() => toggleDay(i)}
                      className={`flex-1 py-2 text-xs font-bold rounded-lg border transition-colors cursor-pointer ${
                        selectedDays.includes(i)
                          ? 'bg-primary border-primary text-white'
                          : 'bg-surface-container border-outline-variant/20 text-on-surface-variant hover:bg-surface-container-high'
                      }`}>{day}</button>
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <button onClick={() => handleSchedule(true)} disabled={saving}
                  className="btn-primary justify-center disabled:opacity-50 disabled:cursor-not-allowed">
                  <span className="material-symbols-outlined text-lg">play_arrow</span>
                  Ativar
                </button>
                <button onClick={() => handleSchedule(false)} disabled={saving}
                  className="btn-ghost justify-center text-error border-error hover:bg-error/10 disabled:opacity-50">
                  <span className="material-symbols-outlined text-lg">stop</span>
                  Parar
                </button>
              </div>
            </div>
          </div>

          {/* Ações imediatas */}
          <div className="border-t border-outline-variant/10 pt-4">
            <h4 className="font-semibold mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-base text-primary">bolt</span>
              Ações Imediatas
            </h4>
            <div className="space-y-3">
              <button onClick={handleTrigger} disabled={triggering}
                className="btn-primary w-full justify-center disabled:opacity-50 disabled:cursor-not-allowed">
                {triggering
                  ? <><span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />Disparando...</>
                  : <><span className="material-symbols-outlined text-lg">send</span>Disparar Envio Agora ({batchSize} emails)</>}
              </button>
              <button onClick={handleStop}
                className="btn-ghost w-full justify-center text-on-surface-variant border-outline-variant/20">
                <span className="material-symbols-outlined text-lg">pause_circle</span>
                Pausar Agendamento
              </button>
              <button onClick={handleClear}
                className="btn-ghost w-full justify-center text-error border-error hover:bg-error/10">
                <span className="material-symbols-outlined text-lg">delete_sweep</span>
                Limpar Lista de Leads da Planilha
              </button>
            </div>
          </div>

          {/* Relatório Diário */}
          <div className="border-t border-outline-variant/10 pt-4">
            <h4 className="font-semibold mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-base text-primary">summarize</span>
              Relatório Diário por Email
            </h4>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-on-surface-variant mb-1">
                  Email para receber o relatório
                </label>
                <input
                  type="email"
                  value={reportEmail}
                  onChange={e => setReportEmail(e.target.value)}
                  placeholder="relatorio@email.com"
                  className="input-field w-full"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => configureReport(true)}
                  disabled={savingReport}
                  className="btn-primary justify-center disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span className="material-symbols-outlined text-lg">check_circle</span>
                  Ativar Relatório
                </button>
                <button
                  onClick={() => configureReport(false)}
                  disabled={savingReport}
                  className="btn-ghost justify-center text-on-surface-variant border-outline-variant/20 disabled:opacity-50"
                >
                  <span className="material-symbols-outlined text-lg">cancel</span>
                  Desativar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </Modal>
  )
}

function StatCard({ label, value, icon, color = 'text-primary' }) {
  return (
    <div className="stat-card">
      <div className="sc-label">
        {label}
        <span className={`material-symbols-outlined ${color}`} style={{ fontSize: 18 }}>{icon}</span>
      </div>
      <div className="sc-val" style={{ fontSize: 22 }}>{(value ?? 0).toLocaleString()}</div>
    </div>
  )
}
