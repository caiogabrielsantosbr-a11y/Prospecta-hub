/**
 * Google Maps Extractor Page - V4 Lime Design
 */
import { useState, useEffect, useRef } from 'react'
import { api } from '../services/api'
import { leadsService, gsheetsService } from '../services/supabase'
import { sendLeadsToSheets } from '../utils/sendLeadsToSheets'
import useTaskStore from '../store/useTaskStore'
import { sessionCache } from '../utils/sessionCache'
import useConfigStore from '../store/useConfigStore'
import toast from 'react-hot-toast'
import LocationSetsModal from '../components/LocationSetsModal'

export default function GMapPage() {
  const { apiUrl } = useConfigStore()
  const [searchTerm, setSearchTerm] = useState('')
  const [delay, setDelay] = useState(5)
  const [selectedCities, setSelectedCities] = useState({})
  const [availableLocations, setAvailableLocations] = useState([])
  const [selectedLocationSet, setSelectedLocationSet] = useState('')
  const [completedCities, setCompletedCities] = useState({}) // Track completed cities
  const [taskId, setTaskId] = useState(null)
  const [isPaused, setIsPaused] = useState(false)
  const [headless, setHeadless] = useState(true) // Navegador oculto por padrão
  const [extractEmails, setExtractEmails] = useState(true) // Extração de email ativada por padrão
  const [autoSyncToSheets, setAutoSyncToSheets] = useState(false)
  const [isStarting, setIsStarting] = useState(false) // Prevent double-click

  // Sync configuration states
  const [syncMode, setSyncMode] = useState('ao_concluir')
  const [syncQuantity, setSyncQuantity] = useState(10)
  const [syncInterval, setSyncInterval] = useState(30)

  const [liveStats, setLiveStats] = useState({
    queue: 0,
    done: 0,
    leads: 0,
    errors: 0,
  })
  const [currentLocation, setCurrentLocation] = useState('São Paulo, BR')
  const [mapMarkers, setMapMarkers] = useState([])

  // Location Sets Management Modal State
  const [showManageModal, setShowManageModal] = useState(false)

  const prevTaskStatusRef = useRef(null)
  const autoSyncIntervalRef = useRef(null)

  const tasks = useTaskStore((s) => s.tasks)
  const currentTask = tasks.find(t => t.id === taskId)

  // Load progress from Supabase for the current location set
  const loadProgress = async (locationSetId) => {
    if (!locationSetId) return
    try {
      const data = await api.getGmapProgress(locationSetId)
      setCompletedCities(data.completed_cities || {})
    } catch (err) {
      console.error('Failed to load progress:', err)
    }
  }

  // Helper: resolve city list from JSONB column, or fallback to Storage JSON
  const resolveCities = async (locationSet) => {
    let locs = locationSet.locations || []

    // Fallback: if JSONB is empty but storage_url exists, fetch from Storage
    if (locs.length === 0 && locationSet.storage_url) {
      try {
        const res = await fetch(locationSet.storage_url)
        if (res.ok) {
          const json = await res.json()
          locs = json.locais || json.locations || []
        }
      } catch (e) {
        console.error('Fallback Storage fetch failed:', e)
      }
    }

    const cities = {}
    locs.forEach(city => { cities[city] = false })
    return cities
  }

  // Load available location sets from Supabase
  useEffect(() => {
    const loadLocations = async () => {
      try {
        const locations = await api.getLocationSets()
        setAvailableLocations(locations)

        if (locations.length > 0) {
          const firstId = locations[0].id
          setSelectedLocationSet(firstId)
          const cities = await resolveCities(locations[0])
          setSelectedCities(cities)
          await loadProgress(firstId)
        }
      } catch (err) {
        console.error('Failed to load locations from Supabase:', err)
        setSelectedCities({
          'São Paulo, SP': false,
          'Rio de Janeiro, RJ': false,
          'Curitiba, PR': false,
          'Belo Horizonte, MG': false,
          'Porto Alegre, RS': false,
          'Salvador, BA': false,
          'Recife, PE': false,
          'Goiânia, GO': false,
        })
      }
    }
    loadLocations()
  }, [])

  // Load sync configuration on mount
  useEffect(() => {
    const loadSyncConfig = async () => {
      try {
        const response = await api.getSyncConfig()
        if (response.success && response.config) {
          setSyncMode(response.config.sync_mode)
          setSyncQuantity(response.config.sync_quantity)
          setSyncInterval(response.config.sync_interval_seconds)
        }
      } catch (err) {
        console.error('Failed to load sync config:', err)
      }
    }
    loadSyncConfig()
  }, [])

  // Save sync configuration
  const saveSyncConfig = async (mode, quantity, interval) => {
    try {
      const response = await api.saveSyncConfig({
        sync_mode: mode,
        sync_quantity: quantity,
        sync_interval_seconds: interval
      })
      if (response.success) {
        toast.success('Configuração salva')
      } else {
        toast.error('Erro ao salvar: ' + response.error)
      }
    } catch (err) {
      toast.error('Erro ao salvar configuração')
    }
  }

  const handleLocationSetChange = async (setId) => {
    setSelectedLocationSet(setId)
    const locationSet = availableLocations.find(loc => loc.id.toString() === setId.toString())
    if (!locationSet) return
    const cities = await resolveCities(locationSet)
    setSelectedCities(cities)
    await loadProgress(setId)
  }

  const toggleCity = (city) => {
    setSelectedCities(prev => ({ ...prev, [city]: !prev[city] }))
  }

  const selectAll = () => {
    const allSelected = {}
    Object.keys(selectedCities).forEach(city => {
      allSelected[city] = true
    })
    setSelectedCities(allSelected)
  }

  const selectNone = () => {
    const noneSelected = {}
    Object.keys(selectedCities).forEach(city => {
      noneSelected[city] = false
    })
    setSelectedCities(noneSelected)
  }

  const selectPending = () => {
    const pendingSelected = {}
    Object.keys(selectedCities).forEach(city => {
      // Select only cities that haven't been completed
      const cityKey = `${selectedLocationSet}:${city}`
      pendingSelected[city] = !completedCities[cityKey]
    })
    setSelectedCities(pendingSelected)
  }

  const markCityCompleted = async (city) => {
    const cityKey = `${selectedLocationSet}:${city}`
    try {
      await api.markCityCompleted({ location_set: selectedLocationSet, city })
      setCompletedCities(prev => ({ ...prev, [cityKey]: true }))
    } catch (err) {
      console.error('Failed to mark city as completed:', err)
    }
  }

  const resetProgress = async () => {
    if (confirm('Deseja resetar o progresso deste conjunto de locais?')) {
      try {
        await api.resetGmapProgress(selectedLocationSet)
        setCompletedCities({})
      } catch (err) {
        console.error('Failed to reset progress:', err)
      }
    }
  }

  const handleStart = async () => {
    if (isStarting || currentTask?.status === 'running') return

    // Reset stats when starting a new extraction
    setLiveStats({
      queue: 0,
      done: 0,
      leads: 0,
      errors: 0,
    })

    // If no cities are selected, select all in order
    let citiesToExtract = Object.entries(selectedCities)
      .filter(([_, selected]) => selected)
      .map(([city]) => city)

    // If none selected, use all cities in order
    if (citiesToExtract.length === 0) {
      citiesToExtract = Object.keys(selectedCities)
    }

    if (!searchTerm || !citiesToExtract.length) return

    setIsStarting(true)
    try {
      const selectedSet = availableLocations.find(loc => loc.id.toString() === selectedLocationSet?.toString())
      const locationSetName = selectedSet?.name || null
      const res = await api.startGmapExtraction(searchTerm, citiesToExtract, delay * 1000, headless, extractEmails, locationSetName)
      setTaskId(res.task_id)
      setIsPaused(false)
    } catch (err) {
      console.error(err)
    } finally {
      setIsStarting(false)
    }
  }

  const triggerAutoSync = async (completedTaskId) => {
    try {
      const leads = await leadsService.getLeadsByTaskId(completedTaskId)
      if (!leads.length) return
      const allWebhooks = await gsheetsService.getWebhooks()
      const activeWebhooks = allWebhooks.filter(w => w.active !== false)
      if (!activeWebhooks.length) {
        toast('Nenhuma planilha ativa para auto-sync', { icon: 'ℹ️' })
        return
      }
      const { totalSent, errors } = await sendLeadsToSheets({ leads, webhooks: activeWebhooks, distribution: 'equal' })
      if (totalSent > 0) toast.success(`Auto-sync: ${totalSent} leads enviados`)
      if (errors.length) toast.error(`Auto-sync com erros: ${errors[0]}`)
    } catch (e) {
      console.error('Auto-sync failed', e)
      toast.error('Erro no auto-sync')
    }
  }

  const handlePause = () => {
    setIsPaused(true)
    // TODO: Implement pause API call
  }

  const handleStop = () => {
    // Reset stats when stopping
    setLiveStats({
      queue: 0,
      done: 0,
      leads: 0,
      errors: 0,
    })
    setTaskId(null)
    setIsPaused(false)
    // TODO: Implement stop API call
  }

  // Update live stats in real-time from task or backend
  useEffect(() => {
    // If we have a current task, use its real stats
    if (currentTask) {
      setLiveStats({
        queue: currentTask.stats?.queue ?? 0,
        done: currentTask.stats?.done ?? 0,
        leads: currentTask.stats?.leads ?? 0,
        errors: currentTask.stats?.errors ?? 0,
      })
    }
  }, [currentTask])

  useEffect(() => {
    const curr = currentTask?.status
    const prev = prevTaskStatusRef.current

    if (autoSyncToSheets && taskId) {
      if (curr === 'running' && prev !== 'running') {
        // Start polling every 60s while running
        autoSyncIntervalRef.current = setInterval(async () => {
          try {
            const allWebhooks = await gsheetsService.getWebhooks()
            const activeWebhooks = allWebhooks.filter(w => w.active !== false)
            if (!activeWebhooks.length) return
            const leads = await leadsService.getLeadsByTaskId(taskId)
            if (!leads.length) return
            const { totalSent } = await sendLeadsToSheets({ leads, webhooks: activeWebhooks, distribution: 'equal' })
            if (totalSent > 0) toast.success(`Auto-sync: ${totalSent} leads → planilhas`)
          } catch (e) { console.error('Auto-sync interval error', e) }
        }, 60000)
      }
      if ((curr === 'completed' || curr === 'done') && prev === 'running') {
        clearInterval(autoSyncIntervalRef.current)
        triggerAutoSync(taskId)
      }
      if (curr === 'stopped' || curr === 'failed') {
        clearInterval(autoSyncIntervalRef.current)
      }
    }
    prevTaskStatusRef.current = curr ?? null
  }, [currentTask?.status])

  // Animate map markers
  useEffect(() => {
    const interval = setInterval(() => {
      const newMarkers = Array.from({ length: 5 }, () => ({
        x: Math.random() * 100,
        y: Math.random() * 100,
        id: Math.random(),
      }))
      setMapMarkers(newMarkers)
    }, 3000)

    return () => clearInterval(interval)
  }, [])

  // Rotate current location
  useEffect(() => {
    if (!currentTask || currentTask.status !== 'running') return

    const cities = Object.keys(selectedCities).filter(city => selectedCities[city])
    if (cities.length === 0) return

    let index = 0
    const interval = setInterval(() => {
      setCurrentLocation(cities[index])
      index = (index + 1) % cities.length
    }, 5000)

    return () => clearInterval(interval)
  }, [currentTask, selectedCities])

  // Use live stats or fallback to current task stats
  const stats = {
    queue: currentTask?.stats?.queue ?? liveStats.queue,
    done: currentTask?.stats?.done ?? liveStats.done,
    leads: currentTask?.stats?.leads ?? liveStats.leads,
    errors: currentTask?.stats?.errors ?? liveStats.errors,
  }

  return (
    <>
      <div className="content-wrapper">
        {/* Stats Dark Grid — 4 cols */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginBottom: 16 }}>
          <div className="stat-card-dark">
            <div className="sc-label">Fila</div>
            <div className="sc-val" style={{ fontSize: 24 }}>{stats.queue.toLocaleString()}</div>
          </div>
          <div className="stat-card-dark">
            <div className="sc-label" style={{ color: 'var(--pro-success)' }}>Concluídos</div>
            <div className="sc-val" style={{ fontSize: 24, color: 'var(--pro-success)' }}>{stats.done.toLocaleString()}</div>
          </div>
          <div className="stat-card-dark">
            <div className="sc-label">Leads</div>
            <div className="sc-val" style={{ fontSize: 24 }}>{stats.leads.toLocaleString()}</div>
          </div>
          <div className="stat-card-dark">
            <div className="sc-label" style={{ color: '#f87171' }}>Erros</div>
            <div className="sc-val" style={{ fontSize: 24, color: '#f87171' }}>{stats.errors.toString().padStart(2, '0')}</div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          {/* Left Column - Config */}
          <div>
            {/* Extractor Config */}
            <div className="form-section" style={{ marginBottom: 16 }}>
              <div className="fs-title">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="4" y1="6" x2="20" y2="6" /><line x1="4" y1="12" x2="14" y2="12" /><line x1="4" y1="18" x2="10" y2="18" /></svg>
                Configuração do Extrator
              </div>

              {/* Search Term */}
              <div style={{ marginBottom: 12 }}>
                <div className="field-label">Termo de Busca</div>
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Ex: Dentistas em São Paulo"
                  style={{ width: '100%' }}
                />
              </div>

              {/* Delay */}
              <div style={{ marginBottom: 12 }}>
                <div className="field-label">Atraso (s)</div>
                <input
                  type="number"
                  value={delay}
                  onChange={(e) => setDelay(parseInt(e.target.value) || 0)}
                  style={{ width: '100%' }}
                />
              </div>

              {/* Toggle Switches */}
              <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
                <div style={{ flex: 1, background: 'var(--pro-surface3)', border: '0.5px solid var(--pro-border)', borderRadius: 8, padding: '10px 12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--pro-text)' }}>{headless ? 'Navegador Oculto' : 'Navegador Visual'}</div>
                    <div style={{ fontSize: 10, color: 'var(--pro-muted)' }}>{headless ? 'Modo headless' : 'Modo visível'}</div>
                  </div>
                  <div className={`pro-toggle ${!headless ? 'on' : ''}`} onClick={() => setHeadless(!headless)} />
                </div>
                <div style={{ flex: 1, background: 'var(--pro-surface3)', border: '0.5px solid var(--pro-border)', borderRadius: 8, padding: '10px 12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--pro-text)' }}>{extractEmails ? 'Extração Ativa' : 'Extração Desativada'}</div>
                    <div style={{ fontSize: 10, color: 'var(--pro-muted)' }}>{extractEmails ? 'Buscando emails' : 'Sem extração'}</div>
                  </div>
                  <div className={`pro-toggle ${extractEmails ? 'on' : ''}`} onClick={() => setExtractEmails(!extractEmails)} />
                </div>
                <div style={{ flex: 1, background: 'var(--pro-surface3)', border: '0.5px solid var(--pro-border)', borderRadius: 8, padding: '10px 12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--pro-text)' }}>{autoSyncToSheets ? 'Enviar p/ Planilhas' : 'Sem Envio Auto'}</div>
                    <div style={{ fontSize: 10, color: 'var(--pro-muted)' }}>{autoSyncToSheets ? 'Sincroniza ao concluir' : 'Desativado'}</div>
                  </div>
                  <div className={`pro-toggle ${autoSyncToSheets ? 'on' : ''}`} onClick={() => setAutoSyncToSheets(!autoSyncToSheets)} />
                </div>
              </div>

              {/* Sync Options Section */}
              {autoSyncToSheets && (
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--pro-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="23 4 23 10 17 10" />
                      <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
                    </svg>
                    Opções de Sincronização
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {/* Option 1: Ao Concluir */}
                    <label style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      padding: '10px 12px',
                      background: syncMode === 'ao_concluir' ? 'var(--pro-surface3)' : 'transparent',
                      border: '0.5px solid var(--pro-border)',
                      borderRadius: 6,
                      cursor: 'pointer'
                    }}>
                      <input
                        type="radio"
                        name="syncMode"
                        value="ao_concluir"
                        checked={syncMode === 'ao_concluir'}
                        onChange={(e) => {
                          setSyncMode(e.target.value)
                          saveSyncConfig(e.target.value, syncQuantity, syncInterval)
                        }}
                        style={{ cursor: 'pointer' }}
                      />
                      <div>
                        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--pro-text)' }}>
                          Sincronizar ao concluir
                        </div>
                        <div style={{ fontSize: 11, color: 'var(--pro-muted)' }}>
                          Envia todos os leads apenas quando a extração finalizar
                        </div>
                      </div>
                    </label>

                    {/* Option 2: Por Quantidade */}
                    <label style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      padding: '10px 12px',
                      background: syncMode === 'por_quantidade' ? 'var(--pro-surface3)' : 'transparent',
                      border: '0.5px solid var(--pro-border)',
                      borderRadius: 6,
                      cursor: 'pointer'
                    }}>
                      <input
                        type="radio"
                        name="syncMode"
                        value="por_quantidade"
                        checked={syncMode === 'por_quantidade'}
                        onChange={(e) => {
                          setSyncMode(e.target.value)
                          saveSyncConfig(e.target.value, syncQuantity, syncInterval)
                        }}
                        style={{ cursor: 'pointer' }}
                      />
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--pro-text)' }}>
                          Sincronizar a cada X leads
                        </div>
                        <div style={{ fontSize: 11, color: 'var(--pro-muted)' }}>
                          Envia um lote a cada quantidade configurada
                        </div>
                      </div>
                      {syncMode === 'por_quantidade' && (
                        <input
                          type="number"
                          value={syncQuantity}
                          onChange={(e) => {
                            const val = parseInt(e.target.value) || 10
                            setSyncQuantity(Math.max(1, Math.min(100, val)))
                          }}
                          onBlur={() => saveSyncConfig(syncMode, syncQuantity, syncInterval)}
                          min="1"
                          max="100"
                          style={{ width: 70, textAlign: 'center', padding: '4px 8px', borderRadius: 4, border: '0.5px solid var(--pro-border)', background: 'var(--pro-surface2)' }}
                          onClick={(e) => e.stopPropagation()}
                        />
                      )}
                    </label>

                    {/* Option 3: Por Tempo */}
                    <label style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      padding: '10px 12px',
                      background: syncMode === 'por_tempo' ? 'var(--pro-surface3)' : 'transparent',
                      border: '0.5px solid var(--pro-border)',
                      borderRadius: 6,
                      cursor: 'pointer'
                    }}>
                      <input
                        type="radio"
                        name="syncMode"
                        value="por_tempo"
                        checked={syncMode === 'por_tempo'}
                        onChange={(e) => {
                          setSyncMode(e.target.value)
                          saveSyncConfig(e.target.value, syncQuantity, syncInterval)
                        }}
                        style={{ cursor: 'pointer' }}
                      />
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--pro-text)' }}>
                          Sincronizar a cada X segundos
                        </div>
                        <div style={{ fontSize: 11, color: 'var(--pro-muted)' }}>
                          Envia um lote a cada intervalo de tempo
                        </div>
                      </div>
                      {syncMode === 'por_tempo' && (
                        <input
                          type="number"
                          value={syncInterval}
                          onChange={(e) => {
                            const val = parseInt(e.target.value) || 30
                            setSyncInterval(Math.max(10, Math.min(300, val)))
                          }}
                          onBlur={() => saveSyncConfig(syncMode, syncQuantity, syncInterval)}
                          min="10"
                          max="300"
                          style={{ width: 70, textAlign: 'center', padding: '4px 8px', borderRadius: 4, border: '0.5px solid var(--pro-border)', background: 'var(--pro-surface2)' }}
                          onClick={(e) => e.stopPropagation()}
                        />
                      )}
                    </label>
                  </div>
                </div>
              )}

              {/* Location Set Selector - Always visible */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">
                    CONJUNTO DE LOCAIS
                  </label>
                  <button
                    onClick={() => setShowManageModal(true)}
                    className="text-[9px] px-2 py-1 rounded bg-surface-container-high hover:bg-surface-container-highest text-on-surface-variant hover:text-primary transition-colors flex items-center gap-1"
                    title="Gerenciar conjuntos"
                  >
                    <span className="material-symbols-outlined text-xs">settings</span>
                    GERENCIAR
                  </button>
                </div>
                {availableLocations.length > 0 ? (
                  <select
                    value={selectedLocationSet}
                    onChange={(e) => handleLocationSetChange(e.target.value)}
                    className="w-full !bg-surface-container-high !border-outline-variant/30 text-sm"
                  >
                    {availableLocations.map(loc => (
                      <option key={loc.id} value={loc.id}>
                        {loc.name} ({loc.location_count} locais)
                      </option>
                    ))}
                  </select>
                ) : (
                  <div className="w-full p-3 rounded bg-surface-container-high border border-outline-variant/15 text-center text-sm text-on-surface-variant">
                    Nenhum conjunto cadastrado
                  </div>
                )}
              </div>

              {/* Target Geographies */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">
                    GEOGRAFIAS ALVO
                  </label>
                  <div className="flex gap-2">
                    <button
                      onClick={selectAll}
                      className="text-[9px] px-2 py-1 rounded bg-surface-container-high hover:bg-surface-container-highest text-on-surface-variant hover:text-primary transition-colors"
                    >
                      TODOS
                    </button>
                    <button
                      onClick={selectNone}
                      className="text-[9px] px-2 py-1 rounded bg-surface-container-high hover:bg-surface-container-highest text-on-surface-variant hover:text-primary transition-colors"
                    >
                      NENHUM
                    </button>
                    <button
                      onClick={selectPending}
                      className="text-[9px] px-2 py-1 rounded bg-surface-container-high hover:bg-surface-container-highest text-on-surface-variant hover:text-primary transition-colors"
                    >
                      PENDENTES
                    </button>
                    <button
                      onClick={resetProgress}
                      className="text-[9px] px-2 py-1 rounded bg-surface-container-high hover:bg-error/20 text-on-surface-variant hover:text-error transition-colors"
                      title="Resetar progresso"
                    >
                      <span className="material-symbols-outlined text-xs">refresh</span>
                    </button>
                  </div>
                </div>
                <div className="text-[9px] text-on-surface-variant/60 italic">
                  * Nenhuma seleção = todos na ordem
                </div>
                {/* Location Checkboxes Grid */}
                <div className="grid grid-cols-2 gap-3 max-h-[300px] overflow-y-auto custom-scrollbar pr-2">
                  {Object.entries(selectedCities).map(([city, selected]) => {
                    const cityKey = `${selectedLocationSet}:${city}`
                    const isCompleted = completedCities[cityKey]

                    return (
                      <label
                        key={city}
                        className={`flex items-center gap-2 cursor-pointer group relative ${isCompleted ? 'opacity-50' : ''}`}
                      >
                        <input
                          type="checkbox"
                          checked={selected}
                          onChange={() => toggleCity(city)}
                          className="w-4 h-4 rounded border-outline-variant bg-surface-container-high checked:bg-primary checked:border-primary cursor-pointer"
                        />
                        <span className={`text-sm ${isCompleted ? 'line-through text-on-surface-variant/50' : 'text-on-surface-variant group-hover:text-primary'} transition-colors`}>
                          {city}
                        </span>
                        {isCompleted && (
                          <span className="material-symbols-outlined text-primary text-xs ml-auto" title="Concluído">
                            check_circle
                          </span>
                        )}
                      </label>
                    )
                  })}
                </div>
              </div>

              {/* Action Buttons */}
              <button
                onClick={handleStart}
                disabled={isStarting || currentTask?.status === 'running'}
                className="btn-primary"
                style={{ width: '100%', justifyContent: 'center', marginBottom: 8, pointerEvents: isStarting || currentTask?.status === 'running' ? 'none' : 'auto' }}
                aria-busy={isStarting}
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polygon points="5 3 19 12 5 21 5 3" /></svg>
                {isStarting ? 'Iniciando...' : 'Iniciar Processo'}
              </button>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                <button
                  onClick={handlePause}
                  disabled={!currentTask || currentTask.status !== 'running'}
                  className="btn-ghost"
                  style={{ justifyContent: 'center', opacity: (!currentTask || currentTask.status !== 'running') ? 0.4 : 1 }}
                >
                  Pausar
                </button>
                <button
                  onClick={handleStop}
                  disabled={!currentTask}
                  className="btn-ghost"
                  style={{ justifyContent: 'center', opacity: !currentTask ? 0.4 : 1 }}
                >
                  Parar
                </button>
              </div>
            </div>
          </div>

          {/* Right Column - Map & Logs */}
          <div>
            {/* Live Map Preview */}
            <div className="map-preview" style={{ height: 200, marginBottom: 12 }}>
              <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(circle at 30% 50%, rgba(232,89,60,0.06) 0%, transparent 60%), radial-gradient(circle at 70% 30%, rgba(196,24,90,0.05) 0%, transparent 50%)' }} />
              <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', opacity: 0.15 }} viewBox="0 0 400 200" preserveAspectRatio="none">
                <path d="M0 50 L400 50 M0 100 L400 100 M0 150 L400 150 M100 0 L100 200 M200 0 L200 200 M300 0 L300 200" stroke="rgba(255,255,255,0.06)" strokeWidth="0.5" fill="none" />
              </svg>

              {/* Map Pins */}
              {mapMarkers.map((marker) => (
                <div key={marker.id} className="map-pin" style={{ top: `${marker.y}%`, left: `${marker.x}%` }} />
              ))}

              {/* Live badge */}
              <div style={{ position: 'absolute', top: 10, left: 10, background: 'rgba(10,10,10,0.85)', border: '0.5px solid var(--pro-border2)', padding: '4px 10px', borderRadius: 6, fontSize: 10, color: 'var(--pro-orange)', display: 'flex', alignItems: 'center', gap: 5, fontWeight: 600 }}>
                <div className="live-dot" />
                Visualização ao Vivo: {currentLocation}
              </div>
            </div>

            {/* Terminal Log */}
            <div className="pro-terminal" style={{ height: 240, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
              <div className="term-head">
                <div className="term-dots">
                  <div className="term-dot" style={{ background: '#f87171' }} />
                  <div className="term-dot" style={{ background: '#fbbf24' }} />
                  <div className="term-dot" style={{ background: '#4ade80' }} />
                </div>
                <span style={{ fontSize: 10, color: 'rgba(74,222,128,0.5)', letterSpacing: '0.1em' }}>LOG DO TERMINAL</span>
              </div>

              <div style={{ flex: 1, overflow: 'auto' }} className="custom-scrollbar">
                {currentTask?.logs?.length > 0 ? (
                  currentTask.logs.slice(-15).map((log, i) => (
                    <div key={i} className="term-line">
                      [{log.time}] <span className="hl">{log.level === 'error' ? 'FALHA' : log.level === 'success' ? 'SUCESSO' : 'PENDENTE'}:</span> {log.message}
                    </div>
                  ))
                ) : (
                  <>
                    <div className="term-line">[09:41:02] <span className="hl">SUCESSO:</span> Inicializando PROSPECTA V4...</div>
                    <div className="term-line">[09:41:03] <span className="hl">SUCESSO:</span> Proxy estabelecido</div>
                    <div className="term-line" style={{ color: 'rgba(251,191,36,0.7)' }}>[09:41:05] PENDENTE: Motor de busca iniciado</div>
                    <div className="term-line">[09:41:08] <span className="hl">SUCESSO:</span> 48 localizações indexadas</div>
                    <div className="term-line">[09:41:10] <span className="hl">SUCESSO:</span> Extraindo: Clínica Sorriso Real</div>
                  </>
                )}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 10, paddingTop: 10, borderTop: '0.5px solid var(--pro-border)' }}>
                <span style={{ color: 'rgba(232,89,60,0.7)' }}>›</span>
                <div className="term-cursor" />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Location Sets Management Modal */}
      <LocationSetsModal
        isOpen={showManageModal}
        onClose={() => setShowManageModal(false)}
        locationSets={availableLocations}
        onRefresh={async (newSetId) => {
          // Reload location sets from Supabase after create/delete
          try {
            const locations = await api.getLocationSets()
            setAvailableLocations(locations)

            if (newSetId) {
              const addedSet = locations.find(loc => loc.id.toString() === newSetId.toString())
              if (addedSet) {
                setSelectedLocationSet(addedSet.id)
                const cities = {}
                const locs = addedSet.locations || []
                locs.forEach(city => {
                  cities[city] = false
                })
                setSelectedCities(cities)
                return
              }
            }

            // If current selection was deleted, select first available
            const currentExists = locations.find(loc => loc.id.toString() === selectedLocationSet?.toString())
            if (!currentExists && locations.length > 0) {
              setSelectedLocationSet(locations[0].id)
              const cities = {}
              const firstLocs = locations[0].locations || []
              firstLocs.forEach(city => {
                cities[city] = false
              })
              setSelectedCities(cities)
            }
          } catch (err) {
            console.error('Failed to reload location sets:', err)
          }
        }}
      />
    </>
  )
}

/* Sub-components removed — stat cards and log lines are now inline using CSS design tokens */
