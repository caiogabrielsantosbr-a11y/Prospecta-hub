import { useMemo, useState, useRef, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Bell, LogOut, User, Settings, Sun, Moon } from 'lucide-react'
import useTaskStore from '../../store/useTaskStore'
import { useAuth } from '../../contexts/AuthContext'
import ConnectionStatus from '../ConnectionStatus'

const ROUTE_META = {
  '/':             { eyebrow: 'Sistema Operacional', title: 'Painel de Controle' },
  '/gmap':         { eyebrow: 'Extração Automática',  title: 'Google Maps Extractor' },
  '/facebook':     { eyebrow: 'Extração Automática',  title: 'Facebook ADS' },
  '/leads':        { eyebrow: 'Gerenciamento',         title: 'Leads' },
  '/inbox':        { eyebrow: 'Comunicação',           title: 'Inbox Gmail' },
  '/profile':      { eyebrow: 'Conta',                 title: 'Meu Perfil' },
  '/admin/config': { eyebrow: 'Sistema',               title: 'Configurações' },
}

export default function TopBar() {
  const tasks = useTaskStore((s) => s.tasks)
  const activeTasks = useMemo(() => tasks.filter(t => t.status === 'running' || t.status === 'paused'), [tasks])
  const { user, profile, signOut } = useAuth()
  const [showMenu, setShowMenu] = useState(false)
  const menuRef = useRef(null)
  const navigate = useNavigate()
  const location = useLocation()

  // Theme state
  const [theme, setTheme] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('prospecta-theme') || 'light'
    }
    return 'light'
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('prospecta-theme', theme)
  }, [theme])

  const toggleTheme = () => setTheme(t => t === 'dark' ? 'light' : 'dark')

  const meta = ROUTE_META[location.pathname] || { eyebrow: 'Prospecta', title: 'Dashboard' }

  useEffect(() => {
    const handler = (e) => { if (menuRef.current && !menuRef.current.contains(e.target)) setShowMenu(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleSignOut = async () => { await signOut(); navigate('/login') }

  const initials = (profile?.full_name || user?.email || 'U')
    .split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase()

  return (
    <header style={{
      height: 56,
      flexShrink: 0,
      borderBottom: '0.5px solid var(--pro-border)',
      background: 'var(--pro-surface)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 28px',
      position: 'sticky',
      top: 0,
      zIndex: 40,
      transition: 'background 0.25s ease, border-color 0.25s ease',
    }}>
      {/* Left: title */}
      <div>
        <div style={{ fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--pro-muted)', fontWeight: 600 }}>
          {meta.eyebrow}
        </div>
        <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--pro-text)', lineHeight: 1.1 }}>
          {meta.title}
        </div>
      </div>

      {/* Right */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        {/* Active tasks badge */}
        {activeTasks.length > 0 && (
          <div className="status-pill" style={{ background: 'rgba(251,191,36,0.12)', color: '#d97706' }}>
            <span className="status-dot animate-pulse" style={{ background: '#d97706' }} />
            {activeTasks.length} processo{activeTasks.length > 1 ? 's' : ''}
          </div>
        )}

        <ConnectionStatus />

        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="btn-icon"
          title={theme === 'dark' ? 'Modo Claro' : 'Modo Escuro'}
          style={{ background: 'transparent', border: 'none' }}
        >
          {theme === 'dark' ? (
            <Sun size={17} strokeWidth={1.75} style={{ color: 'var(--pro-muted)' }} />
          ) : (
            <Moon size={17} strokeWidth={1.75} style={{ color: 'var(--pro-muted)' }} />
          )}
        </button>

        {/* Notification icon */}
        <button className="btn-icon" style={{ background: 'transparent', border: 'none' }}>
          <Bell size={17} strokeWidth={1.75} style={{ color: 'var(--pro-muted)' }} />
        </button>

        {/* Profile menu */}
        <div style={{ position: 'relative' }} ref={menuRef}>
          <button
            onClick={() => setShowMenu(!showMenu)}
            style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
          >
            {profile?.avatar_url ? (
              <img src={profile.avatar_url} alt="Avatar" style={{ width: 32, height: 32, borderRadius: '50%', objectFit: 'cover' }} />
            ) : (
              <div style={{
                width: 32, height: 32, borderRadius: '50%',
                background: 'var(--pro-grad)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 12, fontWeight: 700, color: '#fff',
              }}>
                {initials}
              </div>
            )}
          </button>

          {showMenu && (
            <div
              className="animate-scale-in"
              style={{
                position: 'absolute', right: 0, top: '100%', marginTop: 8,
                width: 230, background: 'var(--pro-surface2)', border: '0.5px solid var(--pro-border2)',
                borderRadius: 12, overflow: 'hidden', boxShadow: '0 20px 60px rgba(0,0,0,0.25)',
                zIndex: 50,
              }}
            >
              <div style={{ padding: '14px 16px', borderBottom: '0.5px solid var(--pro-border)' }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--pro-text)' }}>{profile?.full_name || 'Usuário'}</div>
                <div style={{ fontSize: 12, color: 'var(--pro-muted)', marginTop: 2 }}>{user?.email}</div>
              </div>
              <div style={{ padding: '6px' }}>
                {[
                  { label: 'Meu Perfil', path: '/profile', Icon: User },
                  { label: 'Configurações', path: '/admin/config', Icon: Settings },
                ].map(item => (
                  <button
                    key={item.path}
                    onClick={() => { navigate(item.path); setShowMenu(false) }}
                    style={{
                      width: '100%', padding: '9px 12px', display: 'flex', alignItems: 'center', gap: 8,
                      background: 'none', border: 'none', cursor: 'pointer', borderRadius: 8,
                      fontSize: 14, color: 'var(--pro-muted)', textAlign: 'left',
                    }}
                    onMouseEnter={e => { e.currentTarget.style.background = 'rgba(0,0,0,0.04)'; e.currentTarget.style.color = 'var(--pro-text)' }}
                    onMouseLeave={e => { e.currentTarget.style.background = ''; e.currentTarget.style.color = 'var(--pro-muted)' }}
                  >
                    <item.Icon size={17} strokeWidth={1.75} />
                    {item.label}
                  </button>
                ))}
              </div>
              <div style={{ borderTop: '0.5px solid var(--pro-border)', padding: '6px' }}>
                <button
                  onClick={handleSignOut}
                  style={{
                    width: '100%', padding: '9px 12px', display: 'flex', alignItems: 'center', gap: 8,
                    background: 'none', border: 'none', cursor: 'pointer', borderRadius: 8,
                    fontSize: 14, color: '#dc2626', textAlign: 'left',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(220,38,38,0.06)'}
                  onMouseLeave={e => e.currentTarget.style.background = ''}
                >
                  <LogOut size={17} strokeWidth={1.75} />
                  Sair
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
