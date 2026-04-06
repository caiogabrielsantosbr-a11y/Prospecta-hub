/**
 * TaskManagerBar — floating bottom bar showing active background tasks.
 * Visible on every page, like a music player bar.
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useTaskStore from '../../store/useTaskStore'
import { api } from '../../services/api'

const MODULE_LABELS = {
  gmap: 'GMap',
  facebook_feed: 'FB Feed',
  facebook_contacts: 'FB Contatos',
  emails: 'Emails',
  email_dispatch: 'Disparo',
}

const MODULE_ROUTES = {
  gmap: '/gmap',
  facebook_feed: '/facebook',
  facebook_contacts: '/facebook',
  emails: '/emails',
  email_dispatch: '/dispatch',
}

const STATUS_COLORS = {
  running: 'bg-primary',
  paused: 'bg-secondary',
  completed: 'bg-green-500',
  failed: 'bg-error',
  stopped: 'bg-outline',
}

const STATUS_LABELS = {
  running: 'Em Execução',
  paused: 'Pausado',
  completed: 'Concluído',
  failed: 'Falhou',
  stopped: 'Parado',
}

export default function TaskManagerBar() {
  const [showModal, setShowModal] = useState(false)
  const [isDismissed, setIsDismissed] = useState(false)
  const tasks = useTaskStore((s) => s.tasks)
  const activeTasks = tasks.filter(t => t.status === 'running' || t.status === 'paused')
  const recentTasks = tasks.filter(t => t.status === 'completed' || t.status === 'failed' || t.status === 'stopped')

  // Show bar if there are active tasks OR recent completed tasks (last 3)
  const displayTasks = activeTasks.length > 0 ? activeTasks : recentTasks.slice(-3)
  const isCompleted = activeTasks.length === 0

  // Hide if dismissed or no tasks
  if (isDismissed || displayTasks.length === 0) return null

  const totalProgress = isCompleted ? 100 : (activeTasks.reduce((sum, t) => sum + t.progress, 0) / activeTasks.length)

  const handleDismiss = (e) => {
    e.stopPropagation()
    setIsDismissed(true)
  }

  return (
    <>
      {/* Enhanced Floating Bar */}
      <div className="fixed bottom-6 right-6 z-40 animate-slide-up">
        <div className={`bg-surface-container border-2 ${isCompleted ? 'border-green-500/30' : 'border-primary/30'} rounded-2xl shadow-[0_20px_60px_rgba(0,0,0,0.6)] overflow-hidden min-w-[600px]`}>
          <div
            className="flex items-center justify-between px-6 py-4 cursor-pointer hover:bg-surface-container-high transition-all group"
            onClick={() => setShowModal(true)}
          >
            {/* Left: Progress Circle + Info */}
            <div className="flex items-center gap-4">
              {/* Circular Progress */}
              <div className="relative w-14 h-14">
                <svg className="w-14 h-14 -rotate-90">
                  <circle
                    cx="28"
                    cy="28"
                    r="24"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                    className="text-surface-container-highest"
                  />
                  <circle
                    cx="28"
                    cy="28"
                    r="24"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                    strokeLinecap="round"
                    className={`${isCompleted ? 'text-green-500' : 'text-primary'} transition-all duration-500`}
                    style={{
                      strokeDasharray: `${2 * Math.PI * 24}`,
                      strokeDashoffset: `${2 * Math.PI * 24 * (1 - totalProgress / 100)}`,
                    }}
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  {isCompleted ? (
                    <span className="material-symbols-outlined text-green-500 text-xl">check_circle</span>
                  ) : (
                    <span className="text-xs font-bold text-primary">{Math.round(totalProgress)}%</span>
                  )}
                </div>
              </div>

              {/* Info */}
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className={`w-2 h-2 rounded-full ${isCompleted ? 'bg-green-500' : 'bg-primary animate-pulse'}`} />
                  <span className="text-sm font-bold">
                    {isCompleted ? 'Processamento Concluído' : 'Processamento em Massa'}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-xs text-on-surface-variant">
                  {isCompleted ? (
                    <>
                      <span>Finalizado: {displayTasks.length} tarefa{displayTasks.length > 1 ? 's' : ''}</span>
                      <span className="text-green-500 font-bold">
                        {displayTasks.reduce((sum, t) => sum + (t.stats.leads || 0), 0)} leads
                      </span>
                    </>
                  ) : (
                    <>
                      <span>Ativo: {activeTasks.length} thread{activeTasks.length > 1 ? 's' : ''}</span>
                      <span className="text-primary font-bold">
                        {activeTasks.reduce((sum, t) => sum + (t.stats.leads || 0), 0)}/
                        {activeTasks.reduce((sum, t) => sum + (t.stats.queue || 0) + (t.stats.done || 0), 0)}
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Right: Mini Tasks + Controls */}
            <div className="flex items-center gap-4">
              {/* Mini task indicators */}
              <div className="flex gap-2">
                {displayTasks.slice(0, 3).map(task => (
                  <div key={task.id} className="flex flex-col items-center gap-1">
                    <span className="text-[10px] text-on-surface-variant font-mono">
                      {MODULE_LABELS[task.module] || task.module}
                    </span>
                    <div className="w-12 h-1 rounded-full bg-surface-container-highest overflow-hidden">
                      <div
                        className={`h-full ${
                          task.status === 'completed' ? 'bg-green-500' :
                          task.status === 'failed' ? 'bg-error' :
                          task.status === 'stopped' ? 'bg-outline' :
                          'bg-primary'
                        } transition-all duration-500`}
                        style={{ width: `${task.progress}%` }}
                      />
                    </div>
                  </div>
                ))}
                {displayTasks.length > 3 && (
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-surface-container-highest text-[10px] text-on-surface-variant font-bold">
                    +{displayTasks.length - 3}
                  </div>
                )}
              </div>

              {/* Dismiss button */}
              <button
                onClick={handleDismiss}
                className="p-2 rounded-lg hover:bg-surface-container-highest transition-all"
                title="Fechar"
              >
                <span className="material-symbols-outlined text-on-surface-variant">close</span>
              </button>

              {/* Expand button */}
              <button className="p-2 rounded-lg hover:bg-surface-container-highest transition-all group-hover:bg-surface-container-highest">
                <span className={`material-symbols-outlined ${isCompleted ? 'text-green-500' : 'text-primary'}`}>
                  open_in_full
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Modal */}
      {showModal && <TaskModal tasks={tasks} onClose={() => setShowModal(false)} />}
    </>
  )
}

function TaskRow({ task }) {
  const handlePause = async (e) => {
    e.stopPropagation()
    await api.pauseTask(task.id)
  }

  const handleResume = async (e) => {
    e.stopPropagation()
    await api.resumeTask(task.id)
  }

  const handleStop = async (e) => {
    e.stopPropagation()
    await api.stopTask(task.id)
  }

  return (
    <div className="flex items-center justify-between px-6 py-3 hover:bg-surface-container-low/30 transition-colors animate-slide-up">
      <div className="flex items-center gap-4 flex-1 min-w-0">
        {/* Status dot */}
        <span className={`w-2 h-2 rounded-full shrink-0 ${STATUS_COLORS[task.status] || 'bg-outline'} ${task.status === 'running' ? 'animate-pulse' : ''}`} />

        {/* Info */}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold truncate">{MODULE_LABELS[task.module] || task.module}</span>
            <span className="text-[10px] text-on-surface-variant font-mono">#{task.id}</span>
          </div>
          {/* Progress bar */}
          <div className="w-full h-1 rounded-full bg-surface-container-highest mt-1 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${task.status === 'failed' ? 'bg-error' : 'bg-primary'}`}
              style={{ width: `${task.progress}%` }}
            />
          </div>
        </div>

        {/* Stats */}
        <div className="flex gap-4 text-[10px] font-mono shrink-0">
          {task.stats.leads !== undefined && (
            <span className="text-primary">{task.stats.leads} leads</span>
          )}
          {task.stats.errors > 0 && (
            <span className="text-error">{task.stats.errors} erros</span>
          )}
          <span className="text-on-surface-variant">{Math.round(task.progress)}%</span>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-1 ml-4 shrink-0">
        {task.status === 'running' && (
          <button onClick={handlePause} className="p-1 rounded hover:bg-surface-container-highest transition-all" title="Pausar">
            <span className="material-symbols-outlined text-sm text-on-surface-variant">pause</span>
          </button>
        )}
        {task.status === 'paused' && (
          <button onClick={handleResume} className="p-1 rounded hover:bg-surface-container-highest transition-all" title="Retomar">
            <span className="material-symbols-outlined text-sm text-primary">play_arrow</span>
          </button>
        )}
        {(task.status === 'running' || task.status === 'paused') && (
          <button onClick={handleStop} className="p-1 rounded hover:bg-surface-container-highest transition-all" title="Parar">
            <span className="material-symbols-outlined text-sm text-error">stop</span>
          </button>
        )}
      </div>
    </div>
  )
}

/* ── Task Details Modal ───────────────────────────────────────── */

function TaskModal({ tasks, onClose }) {
  const navigate = useNavigate()
  const activeTasks = tasks.filter(t => t.status === 'running' || t.status === 'paused')
  const completedTasks = tasks.filter(t => t.status === 'completed' || t.status === 'failed' || t.status === 'stopped')

  const handleTaskClick = (task) => {
    const route = MODULE_ROUTES[task.module]
    if (route) {
      navigate(route)
      onClose()
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in" onClick={onClose}>
      <div className="glass-card rounded-2xl shadow-[0_30px_80px_rgba(0,0,0,0.8)] border border-outline-variant/20 w-full max-w-4xl max-h-[80vh] overflow-hidden animate-scale-in" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between px-8 py-6 border-b border-outline-variant/10">
          <div>
            <h3 className="text-2xl font-bold tracking-tight">Processos Ativos</h3>
            <p className="text-sm text-on-surface-variant mt-1">
              {activeTasks.length} em execução • {completedTasks.length} finalizados
            </p>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-surface-container-highest transition-all">
            <span className="material-symbols-outlined text-on-surface-variant">close</span>
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto custom-scrollbar max-h-[calc(80vh-120px)]">
          {/* Active Tasks */}
          {activeTasks.length > 0 && (
            <div className="p-6 space-y-4">
              <h4 className="text-xs font-bold text-primary uppercase tracking-wider">Em Execução</h4>
              {activeTasks.map(task => (
                <TaskDetailCard key={task.id} task={task} onClick={() => handleTaskClick(task)} />
              ))}
            </div>
          )}

          {/* Completed Tasks */}
          {completedTasks.length > 0 && (
            <div className="p-6 space-y-4 border-t border-outline-variant/10">
              <h4 className="text-xs font-bold text-on-surface-variant uppercase tracking-wider">Finalizados</h4>
              {completedTasks.map(task => (
                <TaskDetailCard key={task.id} task={task} onClick={() => handleTaskClick(task)} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

/* ── Task Detail Card ───────────────────────────────────────── */

function TaskDetailCard({ task, onClick }) {
  const handlePause = async (e) => {
    e.stopPropagation()
    await api.pauseTask(task.id)
  }

  const handleResume = async (e) => {
    e.stopPropagation()
    await api.resumeTask(task.id)
  }

  const handleStop = async (e) => {
    e.stopPropagation()
    await api.stopTask(task.id)
  }

  return (
    <div
      className="glass-card p-6 rounded-xl hover:bg-surface-container-low/50 transition-all cursor-pointer group border border-outline-variant/10 hover:border-primary/30"
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className={`w-3 h-3 rounded-full ${STATUS_COLORS[task.status] || 'bg-outline'} ${task.status === 'running' ? 'animate-pulse' : ''}`} />
          <div>
            <div className="flex items-center gap-2">
              <span className="text-base font-bold">{MODULE_LABELS[task.module] || task.module}</span>
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                task.status === 'running' ? 'bg-primary/20 text-primary' :
                task.status === 'paused' ? 'bg-secondary/20 text-secondary' :
                task.status === 'completed' ? 'bg-green-500/20 text-green-500' :
                'bg-error/20 text-error'
              }`}>
                {STATUS_LABELS[task.status] || task.status}
              </span>
            </div>
            <span className="text-[10px] text-on-surface-variant font-mono">#{task.id}</span>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-1">
          {task.status === 'running' && (
            <button onClick={handlePause} className="p-2 rounded-lg hover:bg-surface-container-highest transition-all" title="Pausar">
              <span className="material-symbols-outlined text-sm text-on-surface-variant">pause</span>
            </button>
          )}
          {task.status === 'paused' && (
            <button onClick={handleResume} className="p-2 rounded-lg hover:bg-surface-container-highest transition-all" title="Retomar">
              <span className="material-symbols-outlined text-sm text-primary">play_arrow</span>
            </button>
          )}
          {(task.status === 'running' || task.status === 'paused') && (
            <button onClick={handleStop} className="p-2 rounded-lg hover:bg-surface-container-highest transition-all" title="Parar">
              <span className="material-symbols-outlined text-sm text-error">stop</span>
            </button>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-on-surface-variant">Progresso</span>
          <span className="text-xs font-bold text-primary">{Math.round(task.progress)}%</span>
        </div>
        <div className="w-full h-2 rounded-full bg-surface-container-highest overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${task.status === 'failed' ? 'bg-error' : 'bg-gradient-to-r from-primary-container to-primary'}`}
            style={{ width: `${task.progress}%` }}
          />
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-4 mb-4">
        {task.stats.leads !== undefined && (
          <div className="text-center">
            <div className="text-xl font-bold text-primary">{task.stats.leads}</div>
            <div className="text-[10px] text-on-surface-variant uppercase tracking-wider">Leads</div>
          </div>
        )}
        {task.stats.done !== undefined && (
          <div className="text-center">
            <div className="text-xl font-bold">{task.stats.done}</div>
            <div className="text-[10px] text-on-surface-variant uppercase tracking-wider">Processados</div>
          </div>
        )}
        {task.stats.queue !== undefined && (
          <div className="text-center">
            <div className="text-xl font-bold text-secondary">{task.stats.queue}</div>
            <div className="text-[10px] text-on-surface-variant uppercase tracking-wider">Fila</div>
          </div>
        )}
        {task.stats.errors !== undefined && task.stats.errors > 0 && (
          <div className="text-center">
            <div className="text-xl font-bold text-error">{task.stats.errors}</div>
            <div className="text-[10px] text-on-surface-variant uppercase tracking-wider">Erros</div>
          </div>
        )}
      </div>

      {/* Recent Logs */}
      {task.logs && task.logs.length > 0 && (
        <div className="bg-surface-container/50 rounded-lg p-4">
          <div className="text-[10px] text-on-surface-variant uppercase tracking-wider mb-2 font-bold">Logs Recentes</div>
          <div className="font-mono text-[10px] space-y-1 max-h-24 overflow-y-auto custom-scrollbar">
            {task.logs.slice(-5).map((log, i) => (
              <div key={i} className="flex gap-2">
                <span className="text-on-surface-variant shrink-0">{log.time}</span>
                <span className={`${
                  log.level === 'error' ? 'text-error' :
                  log.level === 'success' ? 'text-primary' :
                  log.level === 'warning' ? 'text-secondary' :
                  'text-on-surface-variant'
                }`}>
                  {log.message}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Click hint */}
      <div className="mt-4 text-center text-[10px] text-on-surface-variant opacity-0 group-hover:opacity-100 transition-opacity">
        <span className="material-symbols-outlined text-xs align-middle">arrow_forward</span> Clique para ir ao módulo
      </div>
    </div>
  )
}
