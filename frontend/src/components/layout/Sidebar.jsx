import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, MapPin, Target, Users, Inbox,
  User, Settings
} from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'

const NAV_ITEMS = [
  { path: '/', icon: LayoutDashboard, label: 'Painel' },
  { path: '/gmap', icon: MapPin, label: 'Google Maps' },
  { path: '/facebook', icon: Target, label: 'Facebook ADS' },
  { path: '/leads', icon: Users, label: 'Leads' },
  { path: '/inbox', icon: Inbox, label: 'Inbox Gmail' },
]

const BOTTOM_ITEMS = [
  { path: '/profile', icon: User, label: 'Perfil' },
  { path: '/admin/config', icon: Settings, label: 'Configurações' },
]

export default function Sidebar() {
  const { theme } = useTheme()

  const navItemStyle = (isActive) => ({
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    padding: '11px 14px',
    borderRadius: 10,
    fontSize: 14,
    fontWeight: isActive ? 600 : 500,
    textDecoration: 'none',
    transition: 'all 0.15s',
    background: isActive ? 'rgba(232,89,60,0.12)' : 'transparent',
    color: isActive ? '#F07A5F' : 'var(--pro-muted)',
  })

  return (
    <aside
      className="fixed left-0 top-0 h-full flex flex-col z-50"
      style={{
        width: 'var(--sidebar-width)',
        background: 'var(--pro-surface)',
        borderRight: '0.5px solid var(--pro-border)',
        transition: 'background 0.25s ease, border-color 0.25s ease',
      }}
    >
      {/* Logo */}
      <div style={{ padding: '22px 20px 18px', borderBottom: '0.5px solid var(--pro-border)' }}>
        <img
          src={theme === 'dark' ? '/logo-branca.png' : '/logo-preta.png'}
          alt="Prospecta"
          style={{
            width: '100%',
            maxWidth: '180px',
            height: 'auto',
            display: 'block'
          }}
        />
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, padding: '14px 12px', display: 'flex', flexDirection: 'column', gap: 3 }}>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              style={({ isActive }) => navItemStyle(isActive)}
              className="sidebar-nav-item"
            >
              <Icon size={18} strokeWidth={1.75} style={{ flexShrink: 0, opacity: 0.7 }} />
              <span>{item.label}</span>
            </NavLink>
          )
        })}

        <div style={{ marginTop: 'auto' }}>
          {BOTTOM_ITEMS.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.path}
                to={item.path}
                style={({ isActive }) => navItemStyle(isActive)}
                className="sidebar-nav-item"
              >
                <Icon size={18} strokeWidth={1.75} style={{ flexShrink: 0, opacity: 0.7 }} />
                <span>{item.label}</span>
              </NavLink>
            )
          })}
        </div>
      </nav>
    </aside>
  )
}
