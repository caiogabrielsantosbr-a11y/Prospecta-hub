/**
 * LocationSetsModal - Modal for managing location sets within GMap Extractor
 */
import { useState } from 'react'
import toast from 'react-hot-toast'
import { api } from '../services/api'

export default function LocationSetsModal({
  isOpen,
  onClose,
  locationSets,
  onRefresh
}) {
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [showPreviewModal, setShowPreviewModal] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [previewData, setPreviewData] = useState(null)
  const [locationSetToDelete, setLocationSetToDelete] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    jsonInput: ''
  })
  const [jsonError, setJsonError] = useState('')

  if (!isOpen) return null

  const validateJson = (input) => {
    const locations = input.split('\n').map(s => s.trim()).filter(Boolean)
    if (locations.length === 0) {
      return { valid: false, error: 'Lista não pode estar vazia' }
    }
    return { valid: true, locations }
  }

  const handleJsonChange = (value) => {
    setFormData({ ...formData, jsonInput: value })
    setJsonError('')
  }

  const handleCreateSubmit = async (e) => {
    e.preventDefault()

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

    const validation = validateJson(formData.jsonInput)
    if (!validation.valid) {
      setJsonError(validation.error)
      toast.error(validation.error)
      return
    }

    setIsCreating(true)
    try {
      const createdRecord = await api.createLocationSet({
        name: formData.name.trim(),
        description: formData.description.trim(),
        locations: validation.locations
      })

      toast.success(`Conjunto criado! ${validation.locations.length} locais adicionados.`)
      setFormData({ name: '', description: '', jsonInput: '' })
      setJsonError('')
      setShowCreateForm(false)
      onRefresh(createdRecord.id)
    } catch (error) {
      console.error('Failed to create location set:', error)
      if (error.message && error.message.includes('duplicate')) {
        toast.error(`Já existe um conjunto com o nome "${formData.name}"`)
      } else {
        toast.error('Erro ao criar conjunto')
      }
    } finally {
      setIsCreating(false)
    }
  }

  const handlePreview = (locationSetId) => {
    const locationSet = locationSets.find(set => set.id === locationSetId)

    if (!locationSet) {
      toast.error('Conjunto não encontrado')
      return
    }

    // Show preview from the locations array already in Supabase response
    const preview = locationSet.locations.slice(0, 10)
    setPreviewData({
      name: locationSet.name,
      preview: preview,
      showing: Math.min(10, locationSet.locations.length),
      total_count: locationSet.locations.length
    })
    setShowPreviewModal(true)
  }

  const handleDeleteClick = (locationSet) => {
    setLocationSetToDelete(locationSet)
    setShowDeleteConfirm(true)
  }

  const handleConfirmDelete = async () => {
    if (!locationSetToDelete) return

    setIsDeleting(true)
    try {
      await api.deleteLocationSet(locationSetToDelete.id)

      toast.success(`Conjunto "${locationSetToDelete.name}" excluído`)
      setShowDeleteConfirm(false)
      setLocationSetToDelete(null)
      onRefresh()
    } catch (error) {
      console.error('Failed to delete location set:', error)
      toast.error('Erro ao excluir conjunto')
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <>
      {/* Main Modal */}
      <div className="modal-overlay" style={{ padding: 16 }}>
        <div className="modal-container" style={{ maxWidth: 800, maxHeight: '90vh', display: 'flex', flexDirection: 'column' }}>
          {/* Header */}
          <div className="modal-header">
            <div>
              <div className="modal-title" style={{ fontSize: 18 }}>
                Gerenciar Conjuntos de Locais
              </div>
              <div style={{ fontSize: 12, color: 'var(--pro-muted)', marginTop: 2 }}>
                Crie e gerencie coleções de localizações para extração
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {!showCreateForm && (
                <button
                  onClick={() => setShowCreateForm(true)}
                  className="btn-primary"
                >
                  <span className="material-symbols-outlined" style={{ fontSize: 16 }}>add</span>
                  Criar Novo
                </button>
              )}
              <button onClick={onClose} className="btn-icon">
                <span className="material-symbols-outlined" style={{ fontSize: 18 }}>close</span>
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {showCreateForm ? (
              <form onSubmit={handleCreateSubmit} className="space-y-4">
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
                    {formData.name.length}/100 caracteres
                  </p>
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
                    Descrição
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Descrição opcional"
                    rows={3}
                    className="w-full resize-none"
                    maxLength={500}
                  />
                  <p className="text-[10px] text-on-surface-variant">
                    {formData.description.length}/500 caracteres
                  </p>
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
                    Locais * <span className="normal-case font-normal">(um por linha)</span>
                  </label>
                  <textarea
                    value={formData.jsonInput}
                    onChange={(e) => handleJsonChange(e.target.value)}
                    placeholder={"São Paulo - SP\nRio de Janeiro - RJ\nCuritiba - PR"}
                    rows={10}
                    className={`w-full resize-none text-sm ${jsonError ? 'border-error' : ''}`}
                    required
                  />
                  {jsonError && (
                    <p className="text-xs text-error flex items-center gap-1">
                      <span className="material-symbols-outlined text-sm">error</span>
                      {jsonError}
                    </p>
                  )}
                </div>

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
                    onClick={() => {
                      setShowCreateForm(false)
                      setFormData({ name: '', description: '', jsonInput: '' })
                      setJsonError('')
                    }}
                    disabled={isCreating}
                    className="btn-ghost"
                  >
                    Cancelar
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-4">
                {locationSets.length === 0 ? (
                  <div className="text-center py-12">
                    <span className="material-symbols-outlined text-6xl text-on-surface-variant mb-4">
                      location_off
                    </span>
                    <p className="text-on-surface-variant">
                      Nenhum conjunto disponível
                    </p>
                  </div>
                ) : (
                  locationSets.map((set) => (
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
                              <span className="material-symbols-outlined text-sm">location_on</span>
                              {set.location_count} locais
                            </span>
                            <span className="flex items-center gap-1">
                              <span className="material-symbols-outlined text-sm">calendar_today</span>
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
                            className="btn-ghost" style={{ fontSize: 12 }}
                          >
                            <span className="material-symbols-outlined text-base">visibility</span>
                            Preview
                          </button>

                          <button
                            onClick={() => handleDeleteClick(set)}
                            className="btn-danger" style={{ fontSize: 12 }}
                          >
                            <span className="material-symbols-outlined text-base">delete</span>
                            Excluir
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Preview Modal */}
      {showPreviewModal && (
        <div className="modal-overlay" style={{ zIndex: 60, padding: 16 }}>
          <div className="modal-container" style={{ maxWidth: 640, maxHeight: '80vh', display: 'flex', flexDirection: 'column' }}>
            <div className="modal-header">
              <div className="modal-title" style={{ fontSize: 18 }}>
                {previewData?.name || 'Preview'}
              </div>
              <button onClick={() => setShowPreviewModal(false)} className="btn-icon">
                <span className="material-symbols-outlined" style={{ fontSize: 18 }}>close</span>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              {previewData ? (
                <div className="space-y-4">
                  <div className="bg-surface-container-low rounded-lg p-4 border border-outline-variant/15">
                    <p className="text-sm text-on-surface-variant">
                      {previewData.showing === previewData.total_count ? (
                        <span className="font-semibold text-on-surface">
                          Mostrando todos os {previewData.total_count} locais
                        </span>
                      ) : (
                        <span className="font-semibold text-on-surface">
                          Mostrando {previewData.showing} de {previewData.total_count} locais
                        </span>
                      )}
                    </p>
                  </div>

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
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && locationSetToDelete && (
        <div className="modal-overlay" style={{ zIndex: 60, padding: 16 }}>
          <div className="modal-container" style={{ maxWidth: 420 }}>
            <div className="modal-header">
              <div className="modal-title" style={{ fontSize: 18 }}>
                Confirmar Exclusão
              </div>
              <button
                onClick={() => setShowDeleteConfirm(false)}
                disabled={isDeleting}
                className="btn-icon"
              >
                <span className="material-symbols-outlined" style={{ fontSize: 18 }}>close</span>
              </button>
            </div>

            <div className="p-6">
              <div className="flex items-start gap-4 mb-4">
                <span className="material-symbols-outlined text-4xl text-error">
                  warning
                </span>
                <div>
                  <p className="text-on-surface mb-2">
                    Tem certeza que deseja excluir <strong>'{locationSetToDelete.name}'</strong>?
                  </p>
                  <p className="text-sm text-on-surface-variant">
                    Esta ação não pode ser desfeita.
                  </p>
                </div>
              </div>
            </div>

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
                onClick={() => setShowDeleteConfirm(false)}
                disabled={isDeleting}
                className="btn-ghost" style={{ flex: 1 }}
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
