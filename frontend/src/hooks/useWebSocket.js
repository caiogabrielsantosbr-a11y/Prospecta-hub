/**
 * WebSocket hook for real-time task updates from the backend.
 * Gracefully handles backend being unavailable.
 */
import { useEffect, useRef } from 'react'
import { io } from 'socket.io-client'
import useTaskStore from '../store/useTaskStore'
import useConfigStore from '../store/useConfigStore'

export default function useWebSocket() {
  const socketRef = useRef(null)
  const apiUrl = useConfigStore((s) => s.apiUrl)
  const setTasks = useTaskStore((s) => s.setTasks)
  const updateTask = useTaskStore((s) => s.updateTask)

  useEffect(() => {
    // Don't connect if URL not configured
    if (!apiUrl) {
      console.log('[WS] No backend URL configured, skipping WebSocket connection')
      return
    }

    console.log('[WS] Connecting to:', apiUrl)
    
    const socket = io(apiUrl, {
      transports: ['websocket', 'polling'],
      reconnectionAttempts: 5,
      reconnectionDelay: 3000,
      timeout: 5000,
    })
    socketRef.current = socket

    socket.on('connect', () => {
      console.log('[WS] Connected:', socket.id)
      useConfigStore.setState({ connectionStatus: 'connected' })
    })

    socket.on('tasks_snapshot', (data) => {
      setTasks(data)
    })

    socket.on('task_update', (data) => {
      updateTask(data)
    })

    socket.on('connect_error', () => {
      console.warn('[WS] Connection error (backend may be unavailable)')
      useConfigStore.setState({ connectionStatus: 'disconnected' })
    })

    socket.on('disconnect', () => {
      console.log('[WS] Disconnected')
      useConfigStore.setState({ connectionStatus: 'disconnected' })
    })

    // Cleanup: disconnect when URL changes or component unmounts
    return () => {
      console.log('[WS] Disconnecting from:', apiUrl)
      socket.disconnect()
    }
  }, [apiUrl, setTasks, updateTask]) // Reconnect when apiUrl changes

  return socketRef
}
