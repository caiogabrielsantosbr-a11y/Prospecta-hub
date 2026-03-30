/**
 * Leads Management Page — Complete lead management interface
 */
import { useState, useEffect } from 'react'
import useConfigStore from '../store/useConfigStore'
import toast from 'react-hot-toast'

export default function LeadsPage() {
  const { apiUrl } = useConfigStore()
  const [leads, setLeads] = useState([])
  const [stats, setStats] = useState(null)
  const [conjuntos, setConjuntos] = useState([])
  const [cidades, setCidades] = useState([])
  
  // Filters
  const [selectedConjunto, setSelectedConjunto] = useState('')
  const [selectedCidade, setSelectedCidade] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  
  // Pagination
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [limit] = useState(50)
  
  // UI State
  const [loading, setLoading] = useState(false)
  const [selectedLeads, setSelectedLeads] = useState(new Set())
  const [editingLead, setEditingLead] = useState(null)
  const [showEditModal, setShowEditModal] = useState(false)

  // Helper function to make API requests
  const apiRequest = async (endpoint, options = {}) => {
    if (!apiUrl) {
      toast.error('Backend não configurado. Configure em Configurações.')
      throw new Error('Backend URL not configured')
    }
    
    const response = await fetch(`${apiUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true',
        ...options.headers
      }
    })
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    return response.json()
  }

  // Load initial data
  useEffect(() => {
    if (apiUrl) {
      loadStats()
      loadConjuntos()
      loadLeads()
    }
  }, [apiUrl])

  // Reload leads when filters or page change
  useEffect(() => {
    if (apiUrl) {
      loadLeads()
    }
  }, [selectedConjunto, selectedCidade, searchTerm, page, apiUrl])

  // Load cidades when conjunto changes
  useEffect(() => {
    if (selectedConjunto && apiUrl) {
      loadCidades(selectedConjunto)
    } else {
      setCidades([])
      setSelectedCidade('')
    }
  }, [selectedConjunto, apiUrl])

  const loadStats = async () => {
    try {
      const data = await apiRequest('/api/leads/stats')
      setStats(data)
    } catch (error) {
      console.error('Error loading stats:', error)
      toast.error('Erro ao carregar estatísticas')
    }
  }

  const loadConjuntos = async () => {
    try {
      const data = await apiRequest('/api/leads/conjuntos')
      setConjuntos(data.conjuntos || [])
    } catch (error) {
      console.error('Error loading conjuntos:', error)
    }
  }

  const loadCidades = async (conjunto) => {
    try {
      const data = await apiRequest(`/api/leads/cidades?conjunto=${encodeURIComponent(conjunto)}`)
      setCidades(data.cidades || [])
    } catch (error) {
      console.error('Error loading cidades:', error)
    }
  }

  const loadLeads = async () => {
    setLoading(true)
    try {
      const offset = (page - 1) * limit
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: offset.toString()
      })
      
      if (selectedConjunto) params.append('conjunto', selectedConjunto)
      if (selectedCidade) params.append('cidade', selectedCidade)
      if (searchTerm) params.append('search', searchTerm)
      
      const data = await apiRequest(`/api/leads?${params}`)
      setLeads(data.leads || [])
      setTotal(data.total || 0)
    } catch (error) {
      console.error('Error loading leads:', error)
      toast.error('Erro ao carregar leads')
      setLeads([])
      setTotal(0)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (leadId) => {
    if (!confirm('Tem certeza que deseja excluir este lead?')) return
    
    try {
      await apiRequest(`/api/leads/${leadId}`, { method: 'DELETE' })
      toast.success('Lead excluído com sucesso')
      loadLeads()
      loadStats()
    } catch (error) {
      console.error('Error deleting lead:', error)
      toast.error('Erro ao excluir lead')
    }
  }

  const handleBulkDelete = async () => {
    if (selectedLeads.size === 0) return
    if (!confirm(`Tem certeza que deseja excluir ${selectedLeads.size} leads?`)) return
    
    try {
      await Promise.all([...selectedLeads].map(id => 
        apiRequest(`/api/leads/${id}`, { method: 'DELETE' })
      ))
      setSelectedLeads(new Set())
      toast.success(`${selectedLeads.size} leads excluídos com sucesso`)
      loadLeads()
      loadStats()
    } catch (error) {
      console.error('Error deleting leads:', error)
      toast.error('Erro ao excluir leads')
    }
  }

  const handleEdit = (lead) => {
    setEditingLead({ ...lead })
    setShowEditModal(true)
  }

  const handleSaveEdit = async () => {
    try {
      await apiRequest(`/api/leads/${editingLead.id}`, {
        method: 'PUT',
        body: JSON.stringify({
          nome: editingLead.nome,
          telefone: editingLead.telefone,
          website: editingLead.website,
          email: editingLead.email,
          endereco: editingLead.endereco,
          cidade: editingLead.cidade
        })
      })
      setShowEditModal(false)
      setEditingLead(null)
      toast.success('Lead atualizado com sucesso')
      loadLeads()
    } catch (error) {
      console.error('Error updating lead:', error)
      toast.error('Erro ao atualizar lead')
    }
  }

  const handleExport = async () => {
    try {
      const data = await apiRequest('/api/leads/export', {
        method: 'POST',
        body: JSON.stringify({
          conjunto: selectedConjunto || undefined,
          cidade: selectedCidade || undefined,
          search: searchTerm || undefined
        })
      })
      
      // Convert to CSV
      const csv = convertToCSV(data.leads)
      downloadCSV(csv, `leads-${Date.now()}.csv`)
      toast.success(`${data.count} leads exportados`)
    } catch (error) {
      console.error('Error exporting leads:', error)
      toast.error('Erro ao exportar leads')
    }
  }

  const convertToCSV = (data) => {
    if (!data || data.length === 0) return ''
    
    const headers = ['ID', 'Nome', 'Telefone', 'Email', 'Website', 'Endereço', 'Cidade', 'Conjunto', 'URL', 'Data']
    const rows = data.map(lead => [
      lead.id,
      lead.nome,
      lead.telefone || '',
      lead.email || '',
      lead.website || '',
      lead.endereco || '',
      lead.cidade || '',
      lead.conjunto_de_locais || '',
      lead.url || '',
      new Date(lead.created_at).toLocaleString('pt-BR')
    ])
    
    return [headers, ...rows].map(row => row.map(cell => `"${cell}"`).join(';')).join('\n')
  }

  const downloadCSV = (csv, filename) => {
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = filename
    link.click()
  }

  const toggleSelectAll = () => {
    if (selectedLeads.size === leads.length) {
      setSelectedLeads(new Set())
    } else {
      setSelectedLeads(new Set(leads.map(l => l.id)))
    }
  }

  const toggleSelect = (id) => {
    const newSelected = new Set(selectedLeads)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelectedLeads(newSelected)
  }

  const totalPages = Math.ceil(total / limit)

  // Show configuration message if backend is not configured
  if (!apiUrl) {
    return (
      <div className="p-8 space-y-8 max-w-[1800px]">
        <div className="flex flex-col gap-1">
          <span className="text-primary font-bold text-[10px] tracking-[0.15em] uppercase">GERENCIAMENTO</span>
          <h2 className="text-3xl font-bold tracking-tight">Leads</h2>
        </div>
        
        <div className="glass-card p-12 rounded-lg text-center">
          <span className="material-symbols-outlined text-6xl text-on-surface-variant opacity-30">settings</span>
          <h3 className="text-xl font-bold mt-4 mb-2">Backend Não Configurado</h3>
          <p className="text-on-surface-variant mb-6">
            Configure a URL do backend em Configurações para visualizar os leads.
          </p>
          <a href="/admin/config" className="btn-primary inline-flex">
            <span className="material-symbols-outlined text-lg">settings</span>
            Ir para Configurações
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 space-y-8 max-w-[1800px]">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <span className="text-primary font-bold text-[10px] tracking-[0.15em] uppercase">GERENCIAMENTO</span>
        <h2 className="text-3xl font-bold tracking-tight">Leads</h2>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
          <StatCard label="Total de Leads" value={stats.total} icon="groups" />
          <StatCard label="Com Telefone" value={stats.with_phone} icon="phone" color="text-primary" />
          <StatCard label="Com Email" value={stats.with_email || 0} icon="email" color="text-secondary" />
          <StatCard label="Com Website" value={stats.with_website} icon="language" color="text-tertiary" />
          <StatCard label="Sem Telefone" value={stats.without_phone} icon="phone_disabled" color="text-error" />
          <StatCard label="Sem Website" value={stats.without_website} icon="link_off" color="text-on-surface-variant" />
        </div>
      )}

      {/* Filters & Actions */}
      <div className="glass-card p-6 rounded-lg space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div className="md:col-span-2">
            <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Buscar</label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value)
                setPage(1)
              }}
              placeholder="Nome, telefone ou website..."
              className="w-full"
            />
          </div>

          {/* Conjunto Filter */}
          <div>
            <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Conjunto</label>
            <select
              value={selectedConjunto}
              onChange={(e) => {
                setSelectedConjunto(e.target.value)
                setPage(1)
              }}
              className="w-full"
            >
              <option value="">Todos</option>
              {conjuntos.map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          {/* Cidade Filter */}
          <div>
            <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Cidade</label>
            <select
              value={selectedCidade}
              onChange={(e) => {
                setSelectedCidade(e.target.value)
                setPage(1)
              }}
              className="w-full"
              disabled={!selectedConjunto}
            >
              <option value="">Todas</option>
              {cidades.map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-4 border-t border-outline-variant/10">
          <div className="flex items-center gap-2">
            {selectedLeads.size > 0 && (
              <>
                <span className="text-sm text-on-surface-variant">{selectedLeads.size} selecionado(s)</span>
                <button onClick={handleBulkDelete} className="btn-ghost text-error border-error hover:bg-error/10">
                  <span className="material-symbols-outlined text-sm">delete</span>
                  Excluir Selecionados
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

      {/* Leads Table */}
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
                      <input
                        type="checkbox"
                        checked={selectedLeads.size === leads.length && leads.length > 0}
                        onChange={toggleSelectAll}
                        className="w-4 h-4"
                      />
                    </th>
                    <th className="p-4 text-left text-xs font-bold uppercase tracking-wider">Nome</th>
                    <th className="p-4 text-left text-xs font-bold uppercase tracking-wider">Telefone</th>
                    <th className="p-4 text-left text-xs font-bold uppercase tracking-wider">Email</th>
                    <th className="p-4 text-left text-xs font-bold uppercase tracking-wider">Website</th>
                    <th className="p-4 text-left text-xs font-bold uppercase tracking-wider">Cidade</th>
                    <th className="p-4 text-left text-xs font-bold uppercase tracking-wider">Conjunto</th>
                    <th className="p-4 text-right text-xs font-bold uppercase tracking-wider">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {leads.map((lead) => (
                    <tr key={lead.id} className="border-b border-outline-variant/5 hover:bg-surface-container-low/30 transition-colors">
                      <td className="p-4">
                        <input
                          type="checkbox"
                          checked={selectedLeads.has(lead.id)}
                          onChange={() => toggleSelect(lead.id)}
                          className="w-4 h-4"
                        />
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
                        ) : (
                          <span className="text-on-surface-variant text-sm">—</span>
                        )}
                      </td>
                      <td className="p-4">
                        {lead.email ? (
                          <a href={`mailto:${lead.email}`} className="text-primary hover:underline flex items-center gap-1">
                            <span className="material-symbols-outlined text-sm">email</span>
                            <span className="truncate max-w-[180px]">{lead.email}</span>
                          </a>
                        ) : (
                          <span className="text-on-surface-variant text-sm">—</span>
                        )}
                      </td>
                      <td className="p-4">
                        {lead.website && lead.website !== 'Sem Website' ? (
                          <a href={lead.website} target="_blank" rel="noopener noreferrer" className="text-secondary hover:underline flex items-center gap-1">
                            <span className="material-symbols-outlined text-sm">language</span>
                            <span className="truncate max-w-[200px]">{lead.website}</span>
                          </a>
                        ) : (
                          <span className="text-on-surface-variant text-sm">—</span>
                        )}
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
                            <a
                              href={lead.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="p-2 rounded-lg hover:bg-surface-container-highest transition-all"
                              title="Ver no Google Maps"
                            >
                              <span className="material-symbols-outlined text-sm text-on-surface-variant">map</span>
                            </a>
                          )}
                          <button
                            onClick={() => handleEdit(lead)}
                            className="p-2 rounded-lg hover:bg-surface-container-highest transition-all"
                            title="Editar"
                          >
                            <span className="material-symbols-outlined text-sm text-on-surface-variant">edit</span>
                          </button>
                          <button
                            onClick={() => handleDelete(lead.id)}
                            className="p-2 rounded-lg hover:bg-surface-container-highest transition-all"
                            title="Excluir"
                          >
                            <span className="material-symbols-outlined text-sm text-error">delete</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between p-4 border-t border-outline-variant/10">
                <div className="text-sm text-on-surface-variant">
                  Mostrando {(page - 1) * limit + 1} a {Math.min(page * limit, total)} de {total} leads
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="p-2 rounded-lg hover:bg-surface-container-highest transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    <span className="material-symbols-outlined">chevron_left</span>
                  </button>
                  <span className="text-sm font-semibold px-4">
                    Página {page} de {totalPages}
                  </span>
                  <button
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="p-2 rounded-lg hover:bg-surface-container-highest transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    <span className="material-symbols-outlined">chevron_right</span>
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Edit Modal */}
      {showEditModal && editingLead && (
        <EditLeadModal
          lead={editingLead}
          onSave={handleSaveEdit}
          onClose={() => {
            setShowEditModal(false)
            setEditingLead(null)
          }}
          onChange={setEditingLead}
        />
      )}
    </div>
  )
}

/* ── Sub-Components ───────────────────────────────────────── */

function StatCard({ label, value, icon, color = 'text-primary' }) {
  return (
    <div className="glass-card p-4 rounded-lg">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">{label}</span>
        <span className={`material-symbols-outlined ${color}`}>{icon}</span>
      </div>
      <div className="text-2xl font-bold">{value?.toLocaleString() || 0}</div>
    </div>
  )
}

function EditLeadModal({ lead, onSave, onClose, onChange }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in" onClick={onClose}>
      <div className="bg-surface-container rounded-2xl shadow-[0_30px_80px_rgba(0,0,0,0.8)] border border-outline-variant/20 w-full max-w-2xl max-h-[80vh] overflow-hidden animate-scale-in" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between px-8 py-6 border-b border-outline-variant/10">
          <h3 className="text-2xl font-bold tracking-tight">Editar Lead</h3>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-surface-container-highest transition-all">
            <span className="material-symbols-outlined text-on-surface-variant">close</span>
          </button>
        </div>

        {/* Content */}
        <div className="p-8 space-y-4 overflow-y-auto max-h-[calc(80vh-180px)]">
          <div>
            <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Nome</label>
            <input
              type="text"
              value={lead.nome}
              onChange={(e) => onChange({ ...lead, nome: e.target.value })}
              className="w-full"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Telefone</label>
            <input
              type="text"
              value={lead.telefone || ''}
              onChange={(e) => onChange({ ...lead, telefone: e.target.value })}
              className="w-full"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Website</label>
            <input
              type="text"
              value={lead.website || ''}
              onChange={(e) => onChange({ ...lead, website: e.target.value })}
              className="w-full"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Email</label>
            <input
              type="email"
              value={lead.email || ''}
              onChange={(e) => onChange({ ...lead, email: e.target.value })}
              className="w-full"
              placeholder="email@exemplo.com"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Endereço</label>
            <input
              type="text"
              value={lead.endereco || ''}
              onChange={(e) => onChange({ ...lead, endereco: e.target.value })}
              className="w-full"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">Cidade</label>
            <input
              type="text"
              value={lead.cidade || ''}
              onChange={(e) => onChange({ ...lead, cidade: e.target.value })}
              className="w-full"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-4 px-8 py-6 border-t border-outline-variant/10">
          <button onClick={onClose} className="btn-ghost">
            Cancelar
          </button>
          <button onClick={onSave} className="btn-primary">
            <span className="material-symbols-outlined text-lg">save</span>
            Salvar
          </button>
        </div>
      </div>
    </div>
  )
}
