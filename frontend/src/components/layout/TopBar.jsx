/**
 * TopBar — sticky header with search and notifications.
 */
import { useMemo } from 'react'
import useTaskStore from '../../store/useTaskStore'
import ThemeToggle from '../ThemeToggle'
import ConnectionStatus from '../ConnectionStatus'

export default function TopBar() {
  const tasks = useTaskStore((s) => s.tasks)
  const activeTasks = useMemo(() => tasks.filter(t => t.status === 'running' || t.status === 'paused'), [tasks])

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
        <button className="text-on-surface-variant hover:text-primary transition-colors cursor-pointer">
          <span className="material-symbols-outlined">settings</span>
        </button>
        <div className="w-8 h-8 rounded-full bg-surface-container-high border border-outline-variant flex items-center justify-center">
          <span className="material-symbols-outlined text-sm text-on-surface-variant">person</span>
        </div>
      </div>
    </header>
  )
}
