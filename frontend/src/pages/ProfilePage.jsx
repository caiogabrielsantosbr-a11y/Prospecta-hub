/**
 * ProfilePage - User profile management
 */
import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import toast from 'react-hot-toast'

export default function ProfilePage() {
  const { user, profile, updateProfile, uploadAvatar, signOut } = useAuth()
  const [editing, setEditing] = useState(false)
  const [formData, setFormData] = useState({
    full_name: profile?.full_name || '',
    backend_url: profile?.backend_url || ''
  })
  const [uploading, setUploading] = useState(false)
  const [saving, setSaving] = useState(false)

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await updateProfile(formData)
      setEditing(false)
    } finally {
      setSaving(false)
    }
  }

  const handleAvatarChange = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validate file type
    if (!file.type.startsWith('image/')) {
      toast.error('Por favor, selecione uma imagem')
      return
    }

    // Validate file size (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
      toast.error('Imagem muito grande. Máximo 2MB')
      return
    }

    setUploading(true)
    try {
      await uploadAvatar(file)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="p-8 space-y-8 max-w-[1200px]">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <span className="text-primary font-bold text-[10px] tracking-[0.15em] uppercase">CONTA</span>
        <h2 className="text-3xl font-bold tracking-tight">Meu Perfil</h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Card */}
        <div className="glass-card rounded-lg p-6 space-y-6">
          {/* Avatar */}
          <div className="flex flex-col items-center gap-4">
            <div className="relative">
              {profile?.avatar_url ? (
                <img
                  src={profile.avatar_url}
                  alt="Avatar"
                  className="w-32 h-32 rounded-full object-cover border-4 border-primary/20"
                />
              ) : (
                <div className="w-32 h-32 rounded-full bg-primary/20 flex items-center justify-center border-4 border-primary/20">
                  <span className="material-symbols-outlined text-6xl text-primary">
                    person
                  </span>
                </div>
              )}
              
              {uploading && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-full">
                  <div className="w-8 h-8 border-4 border-white border-t-transparent rounded-full animate-spin" />
                </div>
              )}
            </div>

            <label className="btn-ghost cursor-pointer">
              <span className="material-symbols-outlined text-lg">upload</span>
              Alterar Foto
              <input
                type="file"
                accept="image/*"
                onChange={handleAvatarChange}
                className="hidden"
                disabled={uploading}
              />
            </label>
          </div>

          {/* User Info */}
          <div className="pt-6 border-t border-outline-variant/10 space-y-3">
            <div>
              <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-1">
                Email
              </label>
              <p className="text-sm">{user?.email}</p>
            </div>

            <div>
              <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-1">
                Membro desde
              </label>
              <p className="text-sm">
                {new Date(profile?.created_at).toLocaleDateString('pt-BR')}
              </p>
            </div>
          </div>

          {/* Sign Out */}
          <button
            onClick={signOut}
            className="btn-ghost w-full justify-center border-error/30 text-error hover:bg-error/10"
          >
            <span className="material-symbols-outlined text-lg">logout</span>
            Sair da Conta
          </button>
        </div>

        {/* Settings Card */}
        <div className="lg:col-span-2 glass-card rounded-lg p-6 space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-bold">Configurações</h3>
            {!editing ? (
              <button
                onClick={() => {
                  setFormData({
                    full_name: profile?.full_name || '',
                    backend_url: profile?.backend_url || ''
                  })
                  setEditing(true)
                }}
                className="btn-ghost"
              >
                <span className="material-symbols-outlined text-lg">edit</span>
                Editar
              </button>
            ) : (
              <div className="flex gap-2">
                <button
                  onClick={() => setEditing(false)}
                  className="btn-ghost"
                  disabled={saving}
                >
                  Cancelar
                </button>
                <button
                  onClick={handleSave}
                  className="btn-primary"
                  disabled={saving}
                >
                  {saving ? (
                    <>
                      <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                      Salvando...
                    </>
                  ) : (
                    <>
                      <span className="material-symbols-outlined text-lg">save</span>
                      Salvar
                    </>
                  )}
                </button>
              </div>
            )}
          </div>

          <div className="space-y-4">
            {/* Full Name */}
            <div>
              <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">
                Nome Completo
              </label>
              {editing ? (
                <input
                  type="text"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleChange}
                  className="w-full"
                  placeholder="Seu nome"
                />
              ) : (
                <p className="text-sm p-3 rounded-lg bg-surface-container-high">
                  {profile?.full_name || 'Não informado'}
                </p>
              )}
            </div>

            {/* Backend URL */}
            <div>
              <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">
                URL do Backend
              </label>
              {editing ? (
                <input
                  type="text"
                  name="backend_url"
                  value={formData.backend_url}
                  onChange={handleChange}
                  className="w-full"
                  placeholder="https://seu-backend.ngrok.io"
                />
              ) : (
                <p className="text-sm p-3 rounded-lg bg-surface-container-high font-mono">
                  {profile?.backend_url || 'Não configurado'}
                </p>
              )}
              <p className="text-xs text-on-surface-variant mt-2">
                Configure a URL do seu backend pessoal para extração de leads
              </p>
            </div>
          </div>

          {/* Info Box */}
          <div className="bg-primary/10 p-4 rounded-lg border border-primary/20">
            <div className="flex gap-3">
              <span className="material-symbols-outlined text-primary text-xl">info</span>
              <div className="flex-1 space-y-2">
                <p className="text-sm font-semibold text-on-surface">Dados Privados</p>
                <p className="text-sm text-on-surface-variant leading-relaxed">
                  Seus leads, tarefas e configurações são privados e visíveis apenas para você.
                  Apenas os conjuntos de locais são compartilhados entre todos os usuários.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
