import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, MapPin, Target, Users, Inbox,
  User, Settings, Plus
} from 'lucide-react'

const NAV_ITEMS = [
  { path: '/',            icon: LayoutDashboard, label: 'Painel' },
  { path: '/gmap',        icon: MapPin,           label: 'Google Maps' },
  { path: '/facebook',    icon: Target,           label: 'Facebook ADS' },
  { path: '/leads',       icon: Users,            label: 'Leads' },
  { path: '/inbox',       icon: Inbox,            label: 'Inbox Gmail' },
]

const BOTTOM_ITEMS = [
  { path: '/profile',     icon: User,             label: 'Perfil' },
  { path: '/admin/config',icon: Settings,         label: 'Configurações' },
]

export default function Sidebar() {
  const navItemStyle = (isActive) => ({
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    padding: '9px 10px',
    borderRadius: 8,
    fontSize: 13,
    fontWeight: 500,
    textDecoration: 'none',
    transition: 'all 0.15s',
    background: isActive ? 'rgba(232,89,60,0.12)' : 'transparent',
    color: isActive ? '#F07A5F' : 'var(--pro-muted)',
  })

  return (
    <aside
      className="fixed left-0 top-0 h-full flex flex-col z-50"
      style={{
        width: 200,
        background: 'var(--pro-surface)',
        borderRight: '0.5px solid var(--pro-border)',
      }}
    >
      {/* Logo */}
      <div style={{ padding: '20px 18px 16px', borderBottom: '0.5px solid var(--pro-border)' }}>
        <div style={{ fontWeight: 800, fontSize: 22, letterSpacing: '-0.01em' }}>
          <span style={{ background: 'var(--pro-grad)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            PRO
          </span>
          <span style={{ color: 'var(--pro-text)' }}>SPECTA</span>
        </div>
        <div style={{ fontSize: 10, color: 'var(--pro-muted2)', marginTop: 2, letterSpacing: '0.06em' }}>
          Prospecting Suite
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, padding: '12px 10px', display: 'flex', flexDirection: 'column', gap: 2 }}>
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
              <Icon size={16} strokeWidth={1.75} style={{ flexShrink: 0, opacity: 0.7 }} />
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
                <Icon size={16} strokeWidth={1.75} style={{ flexShrink: 0, opacity: 0.7 }} />
                <span>{item.label}</span>
              </NavLink>
            )
          })}
        </div>
      </nav>

      {/* CTA Button */}
      <div style={{ padding: '12px 10px' }}>
        <button className="btn-primary" style={{ width: '100%', justifyContent: 'center' }}>
          <Plus size={12} strokeWidth={2.5} />
          Novo Prospecto
        </button>
      </div>
    </aside>
  )
}
