import { useMemo, useState, useRef, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
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
      height: 52,
      flexShrink: 0,
      borderBottom: '0.5px solid rgba(255,255,255,0.08)',
      background: '#161616',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 24px',
      position: 'sticky',
      top: 0,
      zIndex: 40,
    }}>
      {/* Left: eyebrow + title */}
      <div>
        <div style={{ fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'rgba(240,238,233,0.50)', fontWeight: 600 }}>
          {meta.eyebrow}
        </div>
        <div style={{ fontFamily: '"Barlow Condensed", sans-serif', fontSize: 20, fontWeight: 700, color: '#F0EEE9', lineHeight: 1.1 }}>
          {meta.title}
        </div>
      </div>

      {/* Right */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        {/* Active tasks badge */}
        {activeTasks.length > 0 && (
          <div style={{ display:'flex', alignItems:'center', gap:5, padding:'4px 10px', borderRadius:100, background:'rgba(251,191,36,0.12)', fontSize:11, fontWeight:600, color:'#fbbf24' }}>
            <span style={{ width:6, height:6, borderRadius:'50%', background:'#fbbf24' }} className="animate-pulse" />
            {activeTasks.length} processo{activeTasks.length > 1 ? 's' : ''}
          </div>
        )}

        <ConnectionStatus />

        {/* Profile menu */}
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setShowMenu(!showMenu)}
            style={{ display:'flex', alignItems:'center', gap:6, background:'none', border:'none', cursor:'pointer', padding:0 }}
          >
            {profile?.avatar_url ? (
              <img src={profile.avatar_url} alt="Avatar" style={{ width:30, height:30, borderRadius:'50%', objectFit:'cover' }} />
            ) : (
              <div style={{
                width: 30, height: 30, borderRadius: '50%',
                background: 'linear-gradient(135deg,#E8593C,#C4185A)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 11, fontWeight: 700, color: '#fff',
                fontFamily: '"Barlow", sans-serif',
              }}>
                {initials}
              </div>
            )}
            <span style={{ fontSize: 13, fontWeight: 600, color: '#F0EEE9', fontFamily: '"Barlow", sans-serif' }} className="hidden md:block">
              {profile?.full_name || user?.email?.split('@')[0]}
            </span>
          </button>

          {showMenu && (
            <div
              className="animate-scale-in"
              style={{
                position: 'absolute', right: 0, top: '100%', marginTop: 8,
                width: 220, background: '#1F1F1F', border: '0.5px solid rgba(255,255,255,0.14)',
                borderRadius: 12, overflow: 'hidden', boxShadow: '0 20px 60px rgba(0,0,0,0.6)',
                zIndex: 50,
              }}
            >
              <div style={{ padding: '14px 16px', borderBottom: '0.5px solid rgba(255,255,255,0.08)' }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: '#F0EEE9' }}>{profile?.full_name || 'Usuário'}</div>
                <div style={{ fontSize: 11, color: 'rgba(240,238,233,0.50)', marginTop: 2 }}>{user?.email}</div>
              </div>
              <div style={{ padding: '6px' }}>
                {[
                  { label: 'Meu Perfil', path: '/profile', icon: 'person' },
                  { label: 'Configurações', path: '/admin/config', icon: 'settings' },
                ].map(item => (
                  <button
                    key={item.path}
                    onClick={() => { navigate(item.path); setShowMenu(false) }}
                    style={{ width:'100%', padding:'8px 10px', display:'flex', alignItems:'center', gap:8, background:'none', border:'none', cursor:'pointer', borderRadius:8, fontSize:13, color:'rgba(240,238,233,0.50)', fontFamily:'"Barlow",sans-serif', textAlign:'left' }}
                    onMouseEnter={e => { e.currentTarget.style.background='rgba(255,255,255,0.05)'; e.currentTarget.style.color='#F0EEE9' }}
                    onMouseLeave={e => { e.currentTarget.style.background=''; e.currentTarget.style.color='rgba(240,238,233,0.50)' }}
                  >
                    <span className="material-symbols-outlined" style={{ fontSize:16 }}>{item.icon}</span>
                    {item.label}
                  </button>
                ))}
              </div>
              <div style={{ borderTop: '0.5px solid rgba(255,255,255,0.08)', padding: '6px' }}>
                <button
                  onClick={handleSignOut}
                  style={{ width:'100%', padding:'8px 10px', display:'flex', alignItems:'center', gap:8, background:'none', border:'none', cursor:'pointer', borderRadius:8, fontSize:13, color:'#f87171', fontFamily:'"Barlow",sans-serif', textAlign:'left' }}
                  onMouseEnter={e => e.currentTarget.style.background='rgba(248,113,113,0.08)'}
                  onMouseLeave={e => e.currentTarget.style.background=''}
                >
                  <span className="material-symbols-outlined" style={{ fontSize:16 }}>logout</span>
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
