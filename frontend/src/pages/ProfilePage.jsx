/**
 * ProfilePage — User profile management (Screen 06)
 */
import { useState } from 'react'
import { Upload, LogOut, Edit3, Save, AlertCircle } from 'lucide-react'
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
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }))
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
    if (!file.type.startsWith('image/')) { toast.error('Por favor, selecione uma imagem'); return }
    if (file.size > 2 * 1024 * 1024) { toast.error('Imagem muito grande. Máximo 2MB'); return }
    setUploading(true)
    try { await uploadAvatar(file) } finally { setUploading(false) }
  }

  const initials = (profile?.full_name || user?.email || 'U')
    .split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase()

  return (
    <div className="content-wrapper">
      <div style={{ display: 'grid', gridTemplateColumns: '240px 1fr', gap: 20 }}>
        {/* Left: Profile Card */}
        <div className="profile-card">
          {/* Avatar */}
          <div style={{ position: 'relative' }}>
            {profile?.avatar_url ? (
              <img
                src={profile.avatar_url}
                alt="Avatar"
                style={{ width: 72, height: 72, borderRadius: '50%', objectFit: 'cover' }}
              />
            ) : (
              <div className="prof-avatar">{initials}</div>
            )}
            {uploading && (
              <div style={{
                position: 'absolute', inset: 0, display: 'flex', alignItems: 'center',
                justifyContent: 'center', background: 'rgba(0,0,0,0.5)', borderRadius: '50%',
              }}>
                <div style={{ width: 24, height: 24, border: '3px solid #fff', borderTopColor: 'transparent', borderRadius: '50%' }} className="animate-spin" />
              </div>
            )}
          </div>

          <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--pro-text)', marginTop: 12, marginBottom: 4 }}>
            {profile?.full_name || 'Usuário'}
          </div>
          <div style={{ fontSize: 12, color: 'var(--pro-muted)', marginBottom: 4 }}>
            {user?.email}
          </div>
          <div style={{ fontSize: 11, color: 'var(--pro-muted2)', marginBottom: 16 }}>
            Membro desde {profile?.created_at ? new Date(profile.created_at).toLocaleDateString('pt-BR') : '—'}
          </div>

          {/* Upload Button */}
          <label className="btn-outline" style={{ cursor: 'pointer', marginBottom: 8 }}>
            <Upload size={13} strokeWidth={2} />
            Alterar Foto
            <input
              type="file"
              accept="image/*"
              onChange={handleAvatarChange}
              style={{ display: 'none' }}
              disabled={uploading}
            />
          </label>

          {/* Sign Out */}
          <button
            className="btn-outline"
            onClick={signOut}
            style={{ color: '#f87171', borderColor: 'rgba(248,113,113,0.2)' }}
          >
            <LogOut size={13} strokeWidth={2} />
            Sair da Conta
          </button>
        </div>

        {/* Right: Account Settings */}
        <div style={{
          background: 'var(--pro-surface2)', border: '0.5px solid var(--pro-border)',
          borderRadius: 12, padding: 24,
        }}>
          {/* Header */}
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            marginBottom: 20, paddingBottom: 16, borderBottom: '0.5px solid var(--pro-border)',
          }}>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--pro-text)' }}>
              Configurações da Conta
            </div>
            {!editing ? (
              <button
                className="btn-ghost"
                onClick={() => { setFormData({ full_name: profile?.full_name || '', backend_url: profile?.backend_url || '' }); setEditing(true) }}
                style={{ padding: '7px 14px', fontSize: 12 }}
              >
                <Edit3 size={12} strokeWidth={2} />
                Editar
              </button>
            ) : (
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn-ghost" onClick={() => setEditing(false)} disabled={saving} style={{ padding: '7px 14px', fontSize: 12 }}>
                  Cancelar
                </button>
                <button className="btn-primary" onClick={handleSave} disabled={saving} style={{ padding: '7px 14px', fontSize: 12 }}>
                  {saving ? (
                    <><div style={{ width: 14, height: 14, border: '2px solid currentColor', borderTopColor: 'transparent', borderRadius: '50%' }} className="animate-spin" /> Salvando...</>
                  ) : (
                    <><Save size={12} strokeWidth={2} /> Salvar</>
                  )}
                </button>
              </div>
            )}
          </div>

          {/* Fields */}
          <div className="field-label">Nome Completo</div>
          {editing ? (
            <input
              type="text"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              placeholder="Seu nome"
              style={{ width: '100%', marginBottom: 16 }}
            />
          ) : (
            <div style={{
              width: '100%', padding: '9px 12px', background: 'var(--pro-surface3)',
              border: '0.5px solid var(--pro-border)', borderRadius: 8,
              color: 'var(--pro-text)', fontSize: 13, marginBottom: 16,
            }}>
              {profile?.full_name || 'Não informado'}
            </div>
          )}

          <div className="field-label">URL do Backend</div>
          {editing ? (
            <input
              type="text"
              name="backend_url"
              value={formData.backend_url}
              onChange={handleChange}
              placeholder="https://seu-backend.ngrok.io"
              style={{ width: '100%', fontFamily: 'monospace', fontSize: 12, marginBottom: 16 }}
            />
          ) : (
            <div style={{
              width: '100%', padding: '9px 12px', background: 'var(--pro-surface3)',
              border: '0.5px solid var(--pro-border)', borderRadius: 8,
              color: 'var(--pro-muted)', fontSize: 12, fontFamily: 'monospace', marginBottom: 16,
            }}>
              {profile?.backend_url || 'Não configurado'}
            </div>
          )}

          {/* Info Box */}
          <div className="info-box">
            <div style={{ fontSize: 12, fontWeight: 700, color: '#F07A5F', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 6 }}>
              <AlertCircle size={13} strokeWidth={2} />
              Dados Privados
            </div>
            <div style={{ fontSize: 12, color: 'var(--pro-muted)', lineHeight: 1.5 }}>
              Seus leads, tarefas e configurações são privados e visíveis apenas para você.
              Apenas os conjuntos de locais são compartilhados entre todos os usuários.
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
