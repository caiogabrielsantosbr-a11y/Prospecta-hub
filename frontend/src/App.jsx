/**
 * App — Root layout with routing, WebSocket, and global layout.
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'

import { ThemeProvider } from './contexts/ThemeContext'
import { AuthProvider, useAuth } from './contexts/AuthContext'
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
import LoginPage from './pages/LoginPage'
import ProfilePage from './pages/ProfilePage'
import { useEffect } from 'react'

// Protected Route wrapper
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return children
}

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
          <Route path="/profile" element={<ProfilePage />} />
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
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  )
}
