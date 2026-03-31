/**
 * AuthCallbackPage - Handles email confirmation and auth redirects
 */
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../config/supabase'
import toast from 'react-hot-toast'

export default function AuthCallbackPage() {
  const navigate = useNavigate()

  useEffect(() => {
    // Handle the auth callback
    const handleAuthCallback = async () => {
      try {
        // Get the hash from URL
        const hashParams = new URLSearchParams(window.location.hash.substring(1))
        const accessToken = hashParams.get('access_token')
        const type = hashParams.get('type')

        if (accessToken) {
          // Set the session
          const { data, error } = await supabase.auth.setSession({
            access_token: accessToken,
            refresh_token: hashParams.get('refresh_token') || ''
          })

          if (error) throw error

          if (type === 'signup') {
            toast.success('Email confirmado! Bem-vindo!')
          } else {
            toast.success('Login realizado com sucesso!')
          }

          // Redirect to home
          navigate('/', { replace: true })
        } else {
          // No token, redirect to login
          navigate('/login', { replace: true })
        }
      } catch (error) {
        console.error('Auth callback error:', error)
        toast.error('Erro ao confirmar email')
        navigate('/login', { replace: true })
      }
    }

    handleAuthCallback()
  }, [navigate])

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-on-surface-variant">Confirmando email...</p>
      </div>
    </div>
  )
}
