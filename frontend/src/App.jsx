/**
 * App — Root layout with routing, WebSocket, and global layout.
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'

import { AuthProvider, useAuth } from './contexts/AuthContext'
import useWebSocket from './hooks/useWebSocket'
import useConfigStore from './store/useConfigStore'
import Sidebar from './components/layout/Sidebar'
import TopBar from './components/layout/TopBar'
import TaskManagerBar from './components/layout/TaskManagerBar'

import Dashboard from './pages/Dashboard'
import GMapPage from './pages/GMapPage'
import FacebookAdsPage from './pages/FacebookAdsPage'
import LeadsPage from './pages/LeadsPage'
import InboxPage from './pages/InboxPage'
import AdminConfigPage from './pages/AdminConfigPage'
import LoginPage from './pages/LoginPage'
import ProfilePage from './pages/ProfilePage'
import AuthCallbackPage from './pages/AuthCallbackPage'
import { useEffect } from 'react'

// Protected Route wrapper
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div style={{ minHeight:'100vh', display:'flex', alignItems:'center', justifyContent:'center', background:'#0D0D0D' }}>
        <div style={{ width:32, height:32, border:'3px solid rgba(232,89,60,0.2)', borderTopColor:'#E8593C', borderRadius:'50%' }} className="animate-spin" />
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
    <div style={{ display:'flex', height:'100vh', overflow:'hidden', background:'#0D0D0D' }}>
      <Sidebar />
      <main style={{ marginLeft: 200, flex: 1, display:'flex', flexDirection:'column', overflow:'hidden', background:'#0D0D0D' }}>
        <TopBar />
        <div style={{ flex: 1, overflowY: 'auto' }} className="custom-scrollbar">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/gmap" element={<GMapPage />} />
            <Route path="/facebook" element={<FacebookAdsPage />} />
            <Route path="/leads" element={<LeadsPage />} />
            <Route path="/inbox" element={<InboxPage />} />
            <Route path="/admin/config" element={<AdminConfigPage />} />
            <Route path="/profile" element={<ProfilePage />} />
          </Routes>
        </div>
      </main>
      <TaskManagerBar />
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: '#1F1F1F',
            color: '#F0EEE9',
            border: '0.5px solid rgba(255,255,255,0.14)',
            fontFamily: 'Barlow, sans-serif',
            fontSize: '0.875rem',
          },
        }}
      />
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/auth/callback" element={<AuthCallbackPage />} />
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
  )
}
