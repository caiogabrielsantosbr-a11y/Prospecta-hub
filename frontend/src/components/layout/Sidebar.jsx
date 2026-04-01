/**
 * Sidebar — fixed left navigation matching V4 Lime design.
 */
import { NavLink } from 'react-router-dom'

const NAV_ITEMS = [
  { path: '/', icon: 'dashboard', label: 'Painel' },
  { path: '/gmap', icon: 'map', label: 'Google Maps' },
  { path: '/facebook', icon: 'ads_click', label: 'Facebook ADS' },
  { path: '/leads', icon: 'groups', label: 'Leads' },
  { path: '/inbox', icon: 'inbox', label: 'Inbox Gmail' },
  { path: '/profile', icon: 'person', label: 'Perfil' },
  { path: '/admin/config', icon: 'settings', label: 'Configurações' },
]

export default function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 h-full flex flex-col py-6 w-64 border-r border-outline-variant/15 bg-surface/60 backdrop-blur-xl shadow-[0_20px_50px_rgba(0,0,0,0.5)] z-50">
      {/* Logo */}
      <div className="px-6 mb-10">
        <div className="flex items-center gap-3 mb-2">
          <img src="/logo.png" alt="Prospecta HUB" className="h-8" />
        </div>
        <p className="text-on-surface-variant text-xs font-medium tracking-wide">Prospecting Suite</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 space-y-1">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              `flex items-center px-4 py-3 gap-3 rounded-lg transition-all duration-300 ease-out text-sm font-medium tracking-wide ${
                isActive
                  ? 'text-primary bg-surface-container border-r-2 border-primary'
                  : 'text-on-surface-variant hover:text-primary hover:bg-surface-container-low'
              }`
            }
          >
            <span className="material-symbols-outlined">{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Bottom CTA */}
      <div className="px-4 mt-auto">
        <button className="btn-primary w-full justify-center">
          <span className="material-symbols-outlined text-lg">add</span>
          Novo Prospecto
        </button>
      </div>
    </aside>
  )
}
