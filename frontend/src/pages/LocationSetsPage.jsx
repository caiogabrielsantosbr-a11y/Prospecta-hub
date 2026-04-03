/**
 * LocationSetsPage — Admin interface for managing location sets
 */
import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import useConfigStore from '../store/useConfigStore'

export default function LocationSetsPage() {
  const { apiUrl } = useConfigStore()
  const [locationSets, setLocationSets] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    jsonInput: ''
  })
  const [jsonError, setJsonError] = useState('')
  
  // Preview state
  const [showPreview, setShowPreview] = useState(false)
  const [previewData, setPreviewData] = useState(null)
  const [isLoadingPreview, setIsLoadingPreview] = useState(false)
  
  // Delete state
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [locationSetToDelete, setLocationSetToDelete] = useState(null)
  const [isDeleting, setIsDeleting] = useState(false)

  useEffect(() => {
    fetchLocationSets()
  }, [])

  const fetchLocationSets = async () => {
    if (!apiUrl) {
      toast.error('URL do backend não configurada')
      setIsLoading(false)
      return
    }
    
    setIsLoading(true)
    try {
      const response = await fetch(`${apiUrl}/api/locations`, {
        headers: {
          'ngrok-skip-browser-warning': 'true' // Skip ngrok warning page
        }
      })
      if (response.ok) {
        const data = await response.json()
        setLocationSets(data)
      } else {
        toast.error('Falha ao carregar conjuntos de locais')
      }
    } catch (error) {
      console.error('Failed to fetch location sets:', error)
      toast.error('Erro de conexão ao carregar conjuntos')
    } finally {
      setIsLoading(false)
    }
  }

  const validateJson = (jsonString) => {
    if (!jsonString.trim()) {
      return { valid: false, error: 'JSON não pode estar vazio' }
    }

    try {
      // Remove trailing commas before parsing (common mistake)
      const cleanedJson = jsonString.replace(/,(\s*[}\]])/g, '$1')
      const parsed = JSON.parse(cleanedJson)
      
      // Check if it's an array
      if (!Array.isArray(parsed)) {
        return { valid: false, error: 'JSON deve ser um array de strings' }
      }

      // Check if array has at least one element
      if (parsed.length === 0) {
        return { valid: false, error: 'Array deve conter pelo menos 1 local' }
      }

      // Check if all elements are strings
      const nonStrings = parsed.filter(item => typeof item !== 'string')
      if (nonStrings.length > 0) {
        return { valid: false, error: 'Todos os elementos devem ser strings' }
      }

      // Check if all strings are non-empty after trimming
      const emptyStrings = parsed.filter(item => !item.trim())
      if (emptyStrings.length > 0) {
        return { valid: false, error: 'Todos os locais devem ser strings não vazias' }
      }

      return { valid: true, locations: parsed }
    } catch (e) {
      return { valid: false, error: `JSON inválido: ${e.message}` }
    }
  }

  const handleJsonChange = (value) => {
    setFormData({ ...formData, jsonInput: value })
    setJsonError('')
  }

  const handleCreateSubmit = async (e) => {
    e.preventDefault()

    // Check if API is configured
    if (!apiUrl) {
      toast.error('URL do backend não configurada. Configure em Configurações.')
      return
    }

    // Validate form fields
    if (!formData.name.trim()) {
      toast.error('Nome é obrigatório')
      return
    }

    if (formData.name.length < 3 || formData.name.length > 100) {
      toast.error('Nome deve ter entre 3 e 100 caracteres')
      return
    }

    if (formData.description.length > 500) {
      toast.error('Descrição não pode exceder 500 caracteres')
      return
    }

    // Validate JSON
    const validation = validateJson(formData.jsonInput)
    if (!validation.valid) {
      setJsonError(validation.error)
      toast.error(validation.error)
      return
    }

    // Submit to API
    setIsCreating(true)
    try {
      const response = await fetch(`${apiUrl}/api/locations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true' // Skip ngrok warning page
        },
        body: JSON.stringify({
          name: formData.name.trim(),
          description: formData.description.trim(),
          locations: validation.locations
        })
      })

      const data = await response.json()

      if (response.ok) {
        toast.success(`Conjunto criado com sucesso! ${data.location_count} locais adicionados.`)
        
        // Reset form and close
        setFormData({ name: '', description: '', jsonInput: '' })
        setJsonError('')
        setShowCreateForm(false)
        
        // Refresh list
        fetchLocationSets()
      } else {
        // Handle error responses
        const errorMessage = data.detail?.message || data.message || 'Erro ao criar conjunto'
        
        if (data.detail?.error === 'duplicate_name') {
          toast.error(`Já existe um conjunto com o nome "${formData.name}"`)
        } else if (data.detail?.error === 'file_too_large') {
          toast.error('Arquivo JSON excede o limite de 10MB')
        } else if (data.detail?.error === 'invalid_name_length') {
          toast.error('Nome deve ter entre 3 e 100 caracteres')
        } else if (data.detail?.error === 'invalid_description_length') {
          toast.error('Descrição não pode exceder 500 caracteres')
        } else if (data.detail?.error === 'empty_locations') {
          toast.error('Conjunto deve conter pelo menos um local')
        } else if (data.detail?.error === 'invalid_location_format') {
          toast.error('Todos os locais devem ser strings')
        } else {
          toast.error(errorMessage)
        }
      }
    } catch (error) {
      console.error('Failed to create location set:', error)
      toast.error('Erro de conexão ao criar conjunto')
    } finally {
      setIsCreating(false)
    }
  }

  const handleCancelCreate = () => {
    setFormData({ name: '', description: '', jsonInput: '' })
    setJsonError('')
    setShowCreateForm(false)
  }

  const handlePreview = async (locationSetId) => {
    setIsLoadingPreview(true)
    setShowPreview(true)
    setPreviewData(null)
    
    try {
      const response = await fetch(`${apiUrl}/api/locations/${locationSetId}/preview`, {
        headers: {
          'ngrok-skip-browser-warning': 'true' // Skip ngrok warning page
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        setPreviewData(data)
      } else {
        const errorData = await response.json().catch(() => ({}))
        const errorMessage = errorData.detail?.message || errorData.message || 'Erro ao carregar preview'
        toast.error(errorMessage)
        setShowPreview(false)
      }
    } catch (error) {
      console.error('Failed to fetch preview:', error)
      toast.error('Erro de conexão ao carregar preview')
      setShowPreview(false)
    } finally {
      setIsLoadingPreview(false)
    }
  }

  const handleClosePreview = () => {
    setShowPreview(false)
    setPreviewData(null)
  }

  const handleDeleteClick = (locationSet) => {
    setLocationSetToDelete(locationSet)
    setShowDeleteConfirm(true)
  }

  const handleCancelDelete = () => {
    setShowDeleteConfirm(false)
    setLocationSetToDelete(null)
  }

  const handleConfirmDelete = async () => {
    if (!locationSetToDelete) return
    
    setIsDeleting(true)
    try {
      const response = await fetch(`${apiUrl}/api/locations/${locationSetToDelete.id}`, {
        method: 'DELETE',
        headers: {
          'ngrok-skip-browser-warning': 'true' // Skip ngrok warning page
        }
      })
      
      if (response.ok) {
        toast.success(`Conjunto "${locationSetToDelete.name}" excluído com sucesso`)
        
        // Close dialog
        setShowDeleteConfirm(false)
        setLocationSetToDelete(null)
        
        // Refresh list
        fetchLocationSets()
      } else {
        const errorData = await response.json().catch(() => ({}))
        const errorMessage = errorData.detail?.message || errorData.message || 'Erro ao excluir conjunto'
        
        if (response.status === 404) {
          toast.error('Conjunto não encontrado')
        } else {
          toast.error(errorMessage)
        }
      }
    } catch (error) {
      console.error('Failed to delete location set:', error)
      toast.error('Erro de conexão ao excluir conjunto')
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <div className="flex-1 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-on-surface mb-2">
              Conjuntos de Locais
            </h1>
            <p className="text-on-surface-variant">
              Gerencie coleções de localizações geográficas para extração de dados
            </p>
          </div>
          
          {!showCreateForm && (
            <button
              onClick={() => setShowCreateForm(true)}
              className="btn-primary flex items-center gap-2"
            >
              <span className="material-symbols-outlined text-lg">add</span>
              Criar Novo Conjunto
            </button>
          )}
        </div>

        {/* Create Form */}
        {showCreateForm && (
          <div className="bg-surface-container rounded-lg shadow-lg p-6 mb-6">
            <h2 className="text-xl font-bold text-on-surface mb-4">
              Criar Novo Conjunto de Locais
            </h2>
            
            <form onSubmit={handleCreateSubmit} className="space-y-4">
              {/* Name Input */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
                  Nome do Conjunto *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Ex: Capitais do Brasil"
                  className="w-full"
                  maxLength={100}
                  required
                />
                <p className="text-[10px] text-on-surface-variant">
                  {formData.name.length}/100 caracteres (mínimo 3)
                </p>
              </div>

              {/* Description Textarea */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
                  Descrição
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Descrição opcional do conjunto de locais"
                  rows={3}
                  className="w-full resize-none"
                  maxLength={500}
                />
                <p className="text-[10px] text-on-surface-variant">
                  {formData.description.length}/500 caracteres
                </p>
              </div>

              {/* JSON Textarea */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
                  Array JSON de Locais *
                </label>
                <textarea
                  value={formData.jsonInput}
                  onChange={(e) => handleJsonChange(e.target.value)}
                  placeholder='["São Paulo, SP", "Rio de Janeiro, RJ", "Belo Horizonte, MG"]'
                  rows={10}
                  className={`w-full resize-none font-mono text-sm ${jsonError ? 'border-error' : ''}`}
                  required
                />
                {jsonError && (
                  <p className="text-xs text-error flex items-center gap-1">
                    <span className="material-symbols-outlined text-sm">error</span>
                    {jsonError}
                  </p>
                )}
                <p className="text-[10px] text-on-surface-variant">
                  Cole um array JSON com strings de locais. Cada local deve ser uma string não vazia.
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-3 pt-2">
                <button
                  type="submit"
                  disabled={isCreating}
                  className="btn-primary flex items-center gap-2"
                >
                  {isCreating ? (
                    <>
                      <span className="material-symbols-outlined text-lg animate-spin">progress_activity</span>
                      Criando...
                    </>
                  ) : (
                    <>
                      <span className="material-symbols-outlined text-lg">save</span>
                      Criar Conjunto
                    </>
                  )}
                </button>
                
                <button
                  type="button"
                  onClick={handleCancelCreate}
                  disabled={isCreating}
                  className="btn-secondary"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Content */}
        <div className="bg-surface-container rounded-lg shadow-lg p-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-on-surface-variant">Carregando...</div>
            </div>
          ) : locationSets.length === 0 ? (
            <div className="text-center py-12">
              <span className="material-symbols-outlined text-6xl text-on-surface-variant mb-4">
                location_off
              </span>
              <p className="text-on-surface-variant">
                Nenhum conjunto de locais disponível
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {locationSets.map((set) => (
                <div
                  key={set.id}
                  className="bg-surface-container-low rounded-lg p-4 border border-outline-variant/15"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-on-surface mb-1">
                        {set.name}
                      </h3>
                      <p className="text-sm text-on-surface-variant mb-2">
                        {set.description}
                      </p>
                      <div className="flex items-center gap-4 text-xs text-on-surface-variant">
                        <span className="flex items-center gap-1">
                          <span className="material-symbols-outlined text-sm">
                            location_on
                          </span>
                          {set.location_count} locais
                        </span>
                        <span className="flex items-center gap-1">
                          <span className="material-symbols-outlined text-sm">
                            calendar_today
                          </span>
                          {new Date(set.created_at).toLocaleDateString('pt-BR', {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric'
                          })}
                        </span>
                      </div>
                    </div>
                    
                    <div className="ml-4 flex items-center gap-2">
                      <button
                        onClick={() => handlePreview(set.id)}
                        className="btn-secondary flex items-center gap-2"
                      >
                        <span className="material-symbols-outlined text-lg">visibility</span>
                        Preview
                      </button>
                      
                      <button
                        onClick={() => handleDeleteClick(set)}
                        className="btn-secondary text-error hover:bg-error/10 flex items-center gap-2"
                      >
                        <span className="material-symbols-outlined text-lg">delete</span>
                        Excluir
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        {/* Preview Modal */}
        {showPreview && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-surface-container rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] flex flex-col">
              {/* Modal Header */}
              <div className="flex items-center justify-between p-6 border-b border-outline-variant/15">
                <h2 className="text-xl font-bold text-on-surface">
                  {isLoadingPreview ? 'Carregando Preview...' : previewData?.name || 'Preview de Locais'}
                </h2>
                <button
                  onClick={handleClosePreview}
                  className="text-on-surface-variant hover:text-on-surface transition-colors"
                >
                  <span className="material-symbols-outlined text-2xl">close</span>
                </button>
              </div>
              
              {/* Modal Content */}
              <div className="flex-1 overflow-y-auto p-6">
                {isLoadingPreview ? (
                  <div className="flex items-center justify-center py-12">
                    <div className="flex flex-col items-center gap-3">
                      <span className="material-symbols-outlined text-4xl text-primary animate-spin">
                        progress_activity
                      </span>
                      <p className="text-on-surface-variant">Carregando locais...</p>
                    </div>
                  </div>
                ) : previewData ? (
                  <div className="space-y-4">
                    {/* Preview Info */}
                    <div className="bg-surface-container-low rounded-lg p-4 border border-outline-variant/15">
                      <p className="text-sm text-on-surface-variant">
                        {previewData.showing === previewData.total_count ? (
                          <>
                            <span className="font-semibold text-on-surface">
                              Mostrando todos os {previewData.total_count} locais
                            </span>
                          </>
                        ) : (
                          <>
                            <span className="font-semibold text-on-surface">
                              Mostrando {previewData.showing} de {previewData.total_count} locais
                            </span>
                          </>
                        )}
                      </p>
                    </div>
                    
                    {/* Locations List */}
                    <div className="space-y-2">
                      {previewData.preview.map((location, index) => (
                        <div
                          key={index}
                          className="bg-surface-container-low rounded-lg p-3 border border-outline-variant/15 flex items-center gap-3"
                        >
                          <span className="material-symbols-outlined text-primary text-lg">
                            location_on
                          </span>
                          <span className="text-on-surface">{location}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}
              </div>
              
              {/* Modal Footer */}
              <div className="p-6 border-t border-outline-variant/15">
                <button
                  onClick={handleClosePreview}
                  className="btn-secondary w-full"
                >
                  Fechar
                </button>
              </div>
            </div>
          </div>
        )}
        
        {/* Delete Confirmation Modal */}
        {showDeleteConfirm && locationSetToDelete && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-surface-container rounded-lg shadow-xl max-w-md w-full">
              {/* Modal Header */}
              <div className="flex items-center justify-between p-6 border-b border-outline-variant/15">
                <h2 className="text-xl font-bold text-on-surface">
                  Confirmar Exclusão
                </h2>
                <button
                  onClick={handleCancelDelete}
                  disabled={isDeleting}
                  className="text-on-surface-variant hover:text-on-surface transition-colors"
                >
                  <span className="material-symbols-outlined text-2xl">close</span>
                </button>
              </div>
              
              {/* Modal Content */}
              <div className="p-6">
                <div className="flex items-start gap-4 mb-4">
                  <span className="material-symbols-outlined text-4xl text-error">
                    warning
                  </span>
                  <div>
                    <p className="text-on-surface mb-2">
                      Tem certeza que deseja excluir o conjunto <strong>'{locationSetToDelete.name}'</strong>?
                    </p>
                    <p className="text-sm text-on-surface-variant">
                      Esta ação não pode ser desfeita.
                    </p>
                  </div>
                </div>
              </div>
              
              {/* Modal Footer */}
              <div className="p-6 border-t border-outline-variant/15 flex items-center gap-3">
                <button
                  onClick={handleConfirmDelete}
                  disabled={isDeleting}
                  className="btn-primary bg-error hover:bg-error/90 flex items-center gap-2 flex-1"
                >
                  {isDeleting ? (
                    <>
                      <span className="material-symbols-outlined text-lg animate-spin">progress_activity</span>
                      Excluindo...
                    </>
                  ) : (
                    <>
                      <span className="material-symbols-outlined text-lg">delete</span>
                      Excluir
                    </>
                  )}
                </button>
                
                <button
                  onClick={handleCancelDelete}
                  disabled={isDeleting}
                  className="btn-secondary flex-1"
                >
                  Cancelar
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
