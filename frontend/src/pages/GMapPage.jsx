/**
 * Google Maps Extractor Page - V4 Lime Design
 */
import { useState, useEffect } from 'react'
import { api } from '../services/api'
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
  const [isLoadingLocations, setIsLoadingLocations] = useState(false) // Track location loading state
  const [isStarting, setIsStarting] = useState(false) // Prevent double-click
  const [downloadProgress, setDownloadProgress] = useState({ show: false, estimatedSize: null, startTime: null }) // Track download progress
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
  
  const tasks = useTaskStore((s) => s.tasks)
  const currentTask = tasks.find(t => t.id === taskId)

  // Load completed cities from backend
  useEffect(() => {
    const loadProgress = async () => {
      try {
        const response = await fetch('/api/gmap/progress')
        const data = await response.json()
        setCompletedCities(data.completed_cities || {})
      } catch (err) {
        console.error('Failed to load progress:', err)
      }
    }
    loadProgress()
  }, [])

  // Load available location sets from backend
  useEffect(() => {
    const loadLocations = async () => {
      if (!apiUrl) {
        console.warn('Backend URL not configured, using fallback cities')
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
        return
      }
      
      try {
        const response = await fetch(`${apiUrl}/api/locations`, {
          headers: {
            'ngrok-skip-browser-warning': 'true' // Skip ngrok warning page
          }
        })
        const data = await response.json()
        
        // Check if we got the new format (metadata) or old format (direct JSON)
        const isNewFormat = data.length > 0 && data[0].id && data[0].storage_url
        
        if (isNewFormat) {
          // New format: metadata with id, name, description, location_count, storage_url
          setAvailableLocations(data)
          
          // Set first location set as selected, but don't load locations yet (lazy loading)
          if (data.length > 0) {
            setSelectedLocationSet(data[0].id)
            // Load the first location set's data
            await loadLocationSetData(data[0].id, data)
          }
        } else {
          // Old format: direct JSON with nome and locais
          setAvailableLocations(data)
          
          // Set first location set as default
          if (data.length > 0) {
            setSelectedLocationSet(data[0].nome)
            const cities = {}
            data[0].locais.forEach(city => {
              cities[city] = false
            })
            setSelectedCities(cities)
          }
        }
      } catch (err) {
        console.error('Failed to load locations:', err)
        // Fallback to default cities
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
  }, [apiUrl])

  // Helper function to load location set data with session cache
  const loadLocationSetData = async (setId, locationsList = availableLocations) => {
    const locationSet = locationsList.find(loc => loc.id === setId)
    
    if (!locationSet) return
    
    try {
      // Check session cache first
      const cacheKey = setId
      const cachedData = sessionCache.get(cacheKey)
      
      if (cachedData) {
        console.log('Loading location set from cache:', locationSet.name)
        // Use cached data
        const cities = {}
        cachedData.forEach(city => {
          cities[city] = false
        })
        setSelectedCities(cities)
        return
      }
      
      // Cache miss or expired - download from API
      console.log('Downloading location set:', locationSet.name)
      setIsLoadingLocations(true) // Show loading indicator
      
      // Track download start time
      const startTime = Date.now()
      setDownloadProgress({ show: true, estimatedSize: null, startTime })
      
      // Set up a timer to show estimated file size after 2 seconds
      const sizeEstimateTimer = setTimeout(() => {
        const elapsed = Date.now() - startTime
        if (elapsed >= 2000) {
          // Estimate file size based on location count (rough estimate: ~50 bytes per location + overhead)
          const estimatedBytes = locationSet.location_count * 50 + 1000
          const estimatedMB = (estimatedBytes / (1024 * 1024)).toFixed(2)
          setDownloadProgress(prev => ({ ...prev, estimatedSize: estimatedMB }))
        }
      }, 2000)
      
      const response = await fetch(`${apiUrl}/api/locations/${locationSet.id}/full`, {
        headers: {
          'ngrok-skip-browser-warning': 'true' // Skip ngrok warning page
        }
      })
      const data = await response.json()
      
      // Clear the timer
      clearTimeout(sizeEstimateTimer)
      
      // Calculate actual download time
      const downloadTime = Date.now() - startTime
      console.log(`Downloaded location set in ${downloadTime}ms`)
      
      // Store in session cache
      sessionCache.set(cacheKey, data.locations)
      
      // data.locations contains the array of location strings
      const cities = {}
      data.locations.forEach(city => {
        cities[city] = false
      })
      setSelectedCities(cities)
    } catch (err) {
      console.error('Failed to load location set:', err)
    } finally {
      setIsLoadingLocations(false) // Hide loading indicator
      setDownloadProgress({ show: false, estimatedSize: null, startTime: null })
    }
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

  // Fetch real stats from backend periodically
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch('/api/dashboard/stats')
        const data = await response.json()
        
        // Only update leads count from backend if we don't have an active task
        // This prevents showing old lead counts when starting a new extraction
        if (!currentTask && !taskId) {
          setLiveStats({
            queue: 0,
            done: 0,
            leads: data.gmap_leads ?? 0,
            errors: 0,
          })
        }
      } catch (err) {
        console.error('Failed to fetch stats:', err)
      }
    }

    // Fetch immediately only if no task is active
    if (!currentTask && !taskId) {
      fetchStats()
    }

    // Then fetch every 5 seconds
    const interval = setInterval(fetchStats, 5000)

    return () => clearInterval(interval)
  }, [currentTask, taskId])

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

  const handleLocationSetChange = async (setId) => {
    setSelectedLocationSet(setId)
    
    // Find the location set metadata
    const locationSet = availableLocations.find(loc => loc.id === setId || loc.nome === setId)
    
    if (!locationSet) return
    
    // Check if this is the new format (has id and storage_url)
    const isNewFormat = locationSet.id && locationSet.storage_url
    
    if (isNewFormat) {
      // New format: fetch locations from API
      await loadLocationSetData(setId)
    } else {
      // Old format: locations are already in the response
      const cities = {}
      locationSet.locais.forEach(city => {
        cities[city] = false
      })
      setSelectedCities(cities)
    }
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
      await fetch('/api/gmap/progress/mark-completed', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          location_set: selectedLocationSet,
          city: city
        })
      })
      setCompletedCities(prev => ({ ...prev, [cityKey]: true }))
    } catch (err) {
      console.error('Failed to mark city as completed:', err)
    }
  }

  const resetProgress = async () => {
    if (confirm('Deseja resetar o progresso de todas as cidades?')) {
      try {
        await fetch('/api/gmap/progress/reset', { method: 'POST' })
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
      const res = await api.startGmapExtraction(searchTerm, citiesToExtract, delay * 1000, headless, extractEmails)
      setTaskId(res.task_id)
      setIsPaused(false)
    } catch (err) {
      console.error(err)
    } finally {
      setIsStarting(false)
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

  // Use live stats or fallback to current task stats
  const stats = {
    queue: currentTask?.stats?.queue ?? liveStats.queue,
    done: currentTask?.stats?.done ?? liveStats.done,
    leads: currentTask?.stats?.leads ?? liveStats.leads,
    errors: currentTask?.stats?.errors ?? liveStats.errors,
  }

  return (
    <>
      <div className="p-8 space-y-6 max-w-[1800px]">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex flex-col gap-1">
          <h2 className="text-3xl font-bold tracking-tight">
            Extrator Google Maps
          </h2>
          <p className="text-on-surface-variant text-sm">
            Extração automática de leads de empresas locais via inteligência do Google Maps.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${currentTask?.status === 'running' ? 'bg-primary animate-pulse' : 'bg-on-surface-variant'}`} />
          <span className="text-xs font-bold uppercase tracking-wider text-primary">
            {currentTask?.status === 'running' ? 'EXECUTANDO' : 'OCIOSO'}
          </span>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard 
          icon="schedule" 
          label="FILA" 
          value={stats.queue.toLocaleString()} 
          iconColor="text-[#c6e44c]"
        />
        <StatCard 
          icon="check_circle" 
          label="CONCLUÍDOS" 
          value={stats.done.toLocaleString()} 
          iconColor="text-[#4a9eff]"
        />
        <StatCard 
          icon="group" 
          label="LEADS" 
          value={stats.leads.toLocaleString()} 
          iconColor="text-[#c6e44c]"
        />
        <StatCard 
          icon="error" 
          label="ERROS" 
          value={stats.errors.toString().padStart(2, '0')} 
          iconColor="text-[#ff4a4a]"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column - Config */}
        <div className="space-y-6">
          {/* Extractor Config */}
          <div className="glass-card p-6 rounded-lg space-y-6">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-primary">tune</span>
              <h4 className="text-sm font-bold tracking-wider uppercase">Configuração do Extrator</h4>
            </div>

            {/* Search Term */}
            <div className="space-y-2">
              <label className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">
                TERMO DE BUSCA
              </label>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Ex: Dentistas em São Paulo"
                className="w-full !bg-surface-container-high !border-outline-variant/30 text-sm"
              />
            </div>

            {/* Delay */}
            <div className="space-y-2">
              <label className="text-[10px] font-bold text-on-surface-variant uppercase tracking-wider">
                ATRASO (S)
              </label>
              <input
                type="number"
                value={delay}
                onChange={(e) => setDelay(parseInt(e.target.value) || 0)}
                className="w-full !bg-surface-container-high !border-outline-variant/30 text-sm"
              />
            </div>

            {/* Switches */}
            <div className="grid grid-cols-2 gap-4">
              {/* Navegador Visual */}
              <div className="flex items-center justify-between p-3 rounded-lg bg-surface-container-high border border-outline-variant/20 transition-all hover:border-outline-variant/40">
                <div className="flex flex-col">
                  <span className="text-xs font-semibold">{headless ? 'Navegador Oculto' : 'Navegador Visual'}</span>
                  <span className="text-[10px] text-on-surface-variant">{headless ? 'Modo headless' : 'Modo visível'}</span>
                </div>
                <button
                  onClick={() => setHeadless(!headless)}
                  className={`switch-container ${headless ? 'inactive' : 'active'}`}
                >
                  <span className={`switch-thumb ${headless ? 'inactive' : 'active'}`} />
                </button>
              </div>

              {/* Extração de Email */}
              <div className="flex items-center justify-between p-3 rounded-lg bg-surface-container-high border border-outline-variant/20 transition-all hover:border-outline-variant/40">
                <div className="flex flex-col">
                  <span className="text-xs font-semibold">{extractEmails ? 'Extração Ativa' : 'Extração Desativada'}</span>
                  <span className="text-[10px] text-on-surface-variant">{extractEmails ? 'Buscando emails' : 'Sem extração'}</span>
                </div>
                <button
                  onClick={() => setExtractEmails(!extractEmails)}
                  className={`switch-container ${extractEmails ? 'active' : 'inactive'}`}
                >
                  <span className={`switch-thumb ${extractEmails ? 'active' : 'inactive'}`} />
                </button>
              </div>
            </div>

            {/* Location Set Selector */}
            {availableLocations.length > 0 && (
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
                <select
                  value={selectedLocationSet}
                  onChange={(e) => handleLocationSetChange(e.target.value)}
                  className="w-full !bg-surface-container-high !border-outline-variant/30 text-sm"
                >
                  {availableLocations.map(loc => {
                    // Support both new format (id, name, location_count) and old format (nome, locais)
                    const isNewFormat = loc.id && loc.storage_url
                    const key = isNewFormat ? loc.id : loc.nome
                    const displayName = isNewFormat ? loc.name : loc.nome
                    const count = isNewFormat ? loc.location_count : loc.locais.length
                    
                    return (
                      <option key={key} value={key}>
                        {displayName} ({count} locais)
                      </option>
                    )
                  })}
                </select>
              </div>
            )}

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
              {/* Loading Indicator */}
              {isLoadingLocations ? (
                <div className="flex flex-col items-center justify-center py-8 space-y-3">
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                    <span className="text-sm text-on-surface-variant">Loading locations...</span>
                  </div>
                  {downloadProgress.show && downloadProgress.estimatedSize && (
                    <div className="text-xs text-on-surface-variant/70 italic">
                      Estimated file size: ~{downloadProgress.estimatedSize} MB
                    </div>
                  )}
                  {downloadProgress.show && !downloadProgress.estimatedSize && (
                    <div className="text-xs text-on-surface-variant/70 italic">
                      Downloading...
                    </div>
                  )}
                </div>
              ) : (
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
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3 pt-2">
              <button
                onClick={handleStart}
                disabled={isStarting || currentTask?.status === 'running'}
                className="btn-primary flex-1 justify-center disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span className="material-symbols-outlined text-lg">play_arrow</span>
                {isStarting ? 'INICIANDO...' : 'INICIAR PROCESSO'}
              </button>
            </div>

            <div className="flex gap-3">
              <button 
                onClick={handlePause}
                disabled={!currentTask || currentTask.status !== 'running'}
                className="flex-1 flex items-center justify-center gap-3 px-6 py-4 rounded-xl bg-surface-container border border-outline-variant/20 text-on-surface hover:bg-surface-container-high hover:border-outline-variant/40 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <span className="material-symbols-outlined text-2xl font-bold">pause</span>
                <span className="text-base font-bold tracking-widest uppercase">PAUSAR</span>
              </button>
              <button 
                onClick={handleStop}
                disabled={!currentTask}
                className="flex-1 flex items-center justify-center gap-3 px-6 py-4 rounded-xl bg-surface-container border border-error/30 text-error hover:bg-error/10 hover:border-error/50 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <span className="material-symbols-outlined text-2xl font-bold">stop</span>
                <span className="text-base font-bold tracking-widest uppercase">PARAR</span>
              </button>
            </div>
          </div>
        </div>

        {/* Right Column - Map & Logs */}
        <div className="space-y-6">
          {/* Live Map Preview */}
          <div className="glass-card rounded-lg overflow-hidden relative" style={{ height: '400px' }}>
            <div className="absolute inset-0 bg-[#0a0f0a] flex items-center justify-center">
              {/* Map Grid Background */}
              <div className="absolute inset-0 opacity-20" style={{
                backgroundImage: `
                  linear-gradient(rgba(198, 228, 76, 0.1) 1px, transparent 1px),
                  linear-gradient(90deg, rgba(198, 228, 76, 0.1) 1px, transparent 1px)
                `,
                backgroundSize: '40px 40px'
              }} />
              
              {/* Animated Location Markers */}
              {mapMarkers.map((marker) => (
                <div 
                  key={marker.id}
                  className="absolute w-8 h-8 flex items-center justify-center transition-all duration-1000 ease-out"
                  style={{ 
                    left: `${marker.x}%`, 
                    top: `${marker.y}%`,
                    animation: 'fadeInScale 1s ease-out'
                  }}
                >
                  <span className="material-symbols-outlined text-primary text-2xl animate-pulse drop-shadow-[0_0_10px_rgba(198,228,76,0.6)]">
                    location_on
                  </span>
                </div>
              ))}

              {/* Center Location Label */}
              <div className="absolute top-6 left-6 bg-surface-container/90 backdrop-blur-sm px-3 py-1.5 rounded-lg border border-outline-variant/20 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                <span className="text-[10px] font-bold text-on-surface uppercase tracking-wider">
                  VISUALIZAÇÃO AO VIVO: {currentLocation.toUpperCase()}
                </span>
              </div>

              {/* Large Center Pin with pulse animation */}
              <div className="relative animate-pulse-slow">
                <span className="material-symbols-outlined text-primary text-8xl drop-shadow-[0_0_30px_rgba(198,228,76,0.8)]">
                  location_on
                </span>
                {/* Ripple effect */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-32 h-32 rounded-full border-2 border-primary/30 animate-ping" />
                </div>
              </div>
            </div>
          </div>

          {/* Terminal Intelligence Log */}
          <div className="glass-card rounded-lg flex flex-col" style={{ height: '280px' }}>
            <div className="p-4 border-b border-outline-variant/10 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-sm">terminal</span>
                <h4 className="text-[10px] font-bold tracking-widest uppercase">Log de Inteligência do Terminal</h4>
              </div>
              <div className="flex gap-1.5">
                <span className="w-2 h-2 rounded-full bg-error" />
                <span className="w-2 h-2 rounded-full bg-secondary" />
                <span className="w-2 h-2 rounded-full bg-primary" />
              </div>
            </div>
            
            <div className="flex-1 p-4 font-mono text-[10px] space-y-2 custom-scrollbar overflow-y-auto bg-surface-container/30">
              {currentTask?.logs?.length > 0 ? (
                currentTask.logs.slice(-15).map((log, i) => (
                  <div key={i} className="flex gap-3 animate-slide-up">
                    <span className="text-on-surface-variant shrink-0">[{log.time}]</span>
                    <span className={`font-bold ${
                      log.level === 'error' ? 'text-error' : 
                      log.level === 'success' ? 'text-primary' : 
                      'text-secondary'
                    }`}>
                      {log.level === 'error' ? 'FALHA' : log.level === 'success' ? 'SUCESSO' : 'PENDENTE'}:
                    </span>
                    <span className="text-on-surface/80">{log.message}</span>
                  </div>
                ))
              ) : (
                <>
                  <LogLine time="09:41:02" level="success" message="INICIALIZANDO PROSPECTA HUB V4..." />
                  <LogLine time="09:41:03" level="success" message="PROXY ESTABELECIDO: Conexão segura via Node-774." />
                  <LogLine time="09:41:05" level="pending" message="MOTOR DE BUSCA: Procurando 'Dentistas' em SP." />
                  <LogLine time="09:41:08" level="success" message="DADOS ENCONTRADOS: 40 localizações indexadas." />
                  <LogLine time="09:41:10" level="success" message="EXTRAINDO: Clínica Sorriso Real - +55 11 9982..." />
                  <LogLine time="09:41:12" level="success" message="EXTRAINDO: Odonto Master - +55 11 9772..." />
                  <LogLine time="09:41:15" level="pending" message="AGUARDANDO ATRASO: 5 segundos para limitação de taxa." />
                  <LogLine time="09:41:20" level="success" message="EXTRAINDO: Dental Care Sul - +55 11 9662..." />
                  <LogLine time="09:41:22" level="success" message="LEAD SALVO: Lead #2801 adicionado a 'Dentistas_SP_01'." />
                  <LogLine time="09:41:23" level="success" message="EXTRAINDO: Pró-Riso Paulista - +55 11 9662..." />
                  <LogLine time="09:41:25" level="success" message="MAPEAMENTO: Coordenada 23.5505° S, 46.6333° W confirmada." />
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>

    {/* Location Sets Management Modal */}
    <LocationSetsModal
      isOpen={showManageModal}
      onClose={() => setShowManageModal(false)}
      apiUrl={apiUrl}
      locationSets={availableLocations}
      onRefresh={async () => {
        // Reload location sets after create/delete
        try {
          const response = await fetch(`${apiUrl}/api/locations`, {
            headers: {
              'ngrok-skip-browser-warning': 'true'
            }
          })
          const data = await response.json()
          setAvailableLocations(data)
          
          // If current selection was deleted, select first available
          const currentExists = data.find(loc => loc.id === selectedLocationSet || loc.nome === selectedLocationSet)
          if (!currentExists && data.length > 0) {
            const isNewFormat = data[0].id && data[0].storage_url
            const newSelection = isNewFormat ? data[0].id : data[0].nome
            setSelectedLocationSet(newSelection)
            await loadLocationSetData(newSelection, data)
          }
        } catch (err) {
          console.error('Failed to reload location sets:', err)
        }
      }}
    />
    </>
  )
}

/* ── Sub-Components ───────────────────────────────────────── */

function StatCard({ icon, label, value, iconColor }) {
  return (
    <div className="bg-[#1a1d1a] rounded-xl p-5 flex items-center gap-4 border border-white/5">
      <div className={`w-12 h-12 rounded-lg bg-[#0f120f] flex items-center justify-center ${iconColor} border border-white/5`}>
        <span className="material-symbols-outlined text-2xl">{icon}</span>
      </div>
      <div className="flex-1">
        <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1">{label}</p>
        <p className="text-3xl font-bold tracking-tight text-white">{value}</p>
      </div>
    </div>
  )
}

function LogLine({ time, level, message }) {
  const levelColor = level === 'error' ? 'text-error' : level === 'success' ? 'text-primary' : 'text-secondary'
  const levelText = level === 'error' ? 'FALHA' : level === 'success' ? 'SUCESSO' : 'PENDENTE'
  
  return (
    <div className="flex gap-3 animate-slide-up">
      <span className="text-on-surface-variant shrink-0">[{time}]</span>
      <span className={`font-bold ${levelColor}`}>{levelText}:</span>
      <span className="text-on-surface/80">{message}</span>
    </div>
  )
}
