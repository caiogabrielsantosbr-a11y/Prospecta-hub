/**
 * Zustand store for global task state management.
 * Tracks all background tasks across modules.
 */
import { create } from 'zustand'

const useTaskStore = create((set, get) => ({
  tasks: [],
  
  // Replace all tasks (e.g. on snapshot from server)
  setTasks: (tasks) => set({ tasks }),
  
  // Update a single task (from WebSocket event)
  updateTask: (updatedTask) => set((state) => {
    const idx = state.tasks.findIndex(t => t.id === updatedTask.id)
    if (idx >= 0) {
      const newTasks = [...state.tasks]
      newTasks[idx] = updatedTask
      return { tasks: newTasks }
    }
    return { tasks: [...state.tasks, updatedTask] }
  }),

  // Get active tasks
  getActiveTasks: () => {
    return get().tasks.filter(t => t.status === 'running' || t.status === 'paused')
  },

  // Get tasks for a specific module
  getModuleTasks: (module) => {
    return get().tasks.filter(t => t.module === module)
  },
}))

export default useTaskStore
