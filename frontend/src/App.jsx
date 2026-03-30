/**
 * App — Root layout with routing, WebSocket, and global layout.
 */
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'

import { ThemeProvider } from './contexts/ThemeContext'
import useWebSocket from './hooks/useWebSocket'
import useConfigStore from './store/useConfigStore'
import Sidebar from './components/layout/Sidebar'
import TopBar from './components/layout/TopBar'
import TaskManagerBar from './components/layout/TaskManagerBar'

import Dashboard from './pages/Dashboard'
import GMapPage from './pages/GMapPage'
import FacebookAdsPage from './pages/FacebookAdsPage'
import EmailDispatchPage from './pages/EmailDispatchPage'
import LeadsPage from './pages/LeadsPage'
import AdminConfigPage from './pages/AdminConfigPage'
import { useEffect } from 'react'

function AppLayout() {
  useWebSocket()
  const loadFromSupabase = useConfigStore((s) => s.loadFromSupabase)

  // Load configuration on app startup
  useEffect(() => {
    loadFromSupabase()
  }, [loadFromSupabase])

  return (
    <>
      <Sidebar />
      <main className="ml-64 min-h-screen flex flex-col">
        <TopBar />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/gmap" element={<GMapPage />} />
          <Route path="/facebook" element={<FacebookAdsPage />} />
          <Route path="/dispatch" element={<EmailDispatchPage />} />
          <Route path="/leads" element={<LeadsPage />} />
          <Route path="/admin/config" element={<AdminConfigPage />} />
        </Routes>
      </main>
      <TaskManagerBar />

      {/* Background Glow */}
      <div className="bg-glow-primary" />
      <div className="bg-glow-secondary" />

      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: '#1a1919',
            color: '#fff',
            border: '1px solid rgba(73, 72, 71, 0.15)',
            fontFamily: 'Manrope, sans-serif',
            fontSize: '0.875rem',
          },
        }}
      />
    </>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AppLayout />
      </BrowserRouter>
    </ThemeProvider>
  )
}
