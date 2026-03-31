/**
 * TopBar — sticky header with search and notifications.
 */
import { useMemo, useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import useTaskStore from '../../store/useTaskStore'
import { useAuth } from '../../contexts/AuthContext'
import ThemeToggle from '../ThemeToggle'
import ConnectionStatus from '../ConnectionStatus'

export default function TopBar() {
  const tasks = useTaskStore((s) => s.tasks)
  const activeTasks = useMemo(() => tasks.filter(t => t.status === 'running' || t.status === 'paused'), [tasks])
  const { user, profile, signOut } = useAuth()
  const [showProfileMenu, setShowProfileMenu] = useState(false)
  const menuRef = useRef(null)
  const navigate = useNavigate()

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowProfileMenu(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSignOut = async () => {
    await signOut()
    navigate('/login')
  }

  return (
    <header className="w-full h-16 border-b border-outline-variant/15 sticky top-0 z-40 bg-surface/60 backdrop-blur-2xl flex items-center justify-between px-8">
      <div className="flex items-center gap-6">
        {/* Active Tasks Badge */}
        {activeTasks.length > 0 && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-primary/10 cursor-pointer hover:bg-primary/15 transition-colors">
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            <span className="text-primary text-xs font-bold">
              {activeTasks.length} {activeTasks.length === 1 ? 'processo' : 'processos'} ativo{activeTasks.length > 1 ? 's' : ''}
            </span>
          </div>
        )}
      </div>

      <div className="flex items-center gap-4">
        <ConnectionStatus />
        <button className="text-on-surface-variant hover:text-primary transition-colors cursor-pointer">
          <span className="material-symbols-outlined">notifications</span>
        </button>
        <ThemeToggle />
        
        {/* Profile Menu */}
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setShowProfileMenu(!showProfileMenu)}
            className="flex items-center gap-2 hover:opacity-80 transition-opacity"
          >
            {profile?.avatar_url ? (
              <img
                src={profile.avatar_url}
                alt="Avatar"
                className="w-8 h-8 rounded-full object-cover border border-outline-variant"
              />
            ) : (
              <div className="w-8 h-8 rounded-full bg-surface-container-high border border-outline-variant flex items-center justify-center">
                <span className="material-symbols-outlined text-sm text-on-surface-variant">person</span>
              </div>
            )}
            <span className="text-sm font-semibold hidden md:block">
              {profile?.full_name || user?.email?.split('@')[0]}
            </span>
            <span className="material-symbols-outlined text-sm text-on-surface-variant">
              {showProfileMenu ? 'expand_less' : 'expand_more'}
            </span>
          </button>

          {/* Dropdown Menu */}
          {showProfileMenu && (
            <div className="absolute right-0 mt-2 w-64 glass-card rounded-lg shadow-xl border border-outline-variant/20 overflow-hidden animate-scale-in">
              {/* User Info */}
              <div className="p-4 border-b border-outline-variant/10">
                <p className="font-semibold">{profile?.full_name || 'Usuário'}</p>
                <p className="text-xs text-on-surface-variant truncate">{user?.email}</p>
              </div>

              {/* Menu Items */}
              <div className="py-2">
                <button
                  onClick={() => {
                    navigate('/profile')
                    setShowProfileMenu(false)
                  }}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-surface-container-high transition-colors flex items-center gap-3"
                >
                  <span className="material-symbols-outlined text-lg">person</span>
                  Meu Perfil
                </button>
                <button
                  onClick={() => {
                    navigate('/admin/config')
                    setShowProfileMenu(false)
                  }}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-surface-container-high transition-colors flex items-center gap-3"
                >
                  <span className="material-symbols-outlined text-lg">settings</span>
                  Configurações
                </button>
              </div>

              {/* Sign Out */}
              <div className="border-t border-outline-variant/10 p-2">
                <button
                  onClick={handleSignOut}
                  className="w-full px-4 py-2 text-left text-sm text-error hover:bg-error/10 transition-colors flex items-center gap-3 rounded-lg"
                >
                  <span className="material-symbols-outlined text-lg">logout</span>
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
