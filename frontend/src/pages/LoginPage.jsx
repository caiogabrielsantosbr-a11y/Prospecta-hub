/**
 * LoginPage - User authentication page with login and signup
 */
import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { Navigate } from 'react-router-dom'

export default function LoginPage() {
  const { user, loading, signIn, signUp } = useAuth()
  const [isSignUp, setIsSignUp] = useState(false)
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    fullName: ''
  })
  const [submitting, setSubmitting] = useState(false)

  // Redirect if already logged in
  if (!loading && user) {
    return <Navigate to="/" replace />
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)

    try {
      if (isSignUp) {
        await signUp(formData.email, formData.password, formData.fullName)
      } else {
        await signIn(formData.email, formData.password)
      }
    } finally {
      setSubmitting(false)
    }
  }

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      {/* Background Glow */}
      <div className="bg-glow-primary" />
      <div className="bg-glow-secondary" />

      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold tracking-tight mb-2">
            Lead Prospecting
          </h1>
          <p className="text-on-surface-variant">
            {isSignUp ? 'Crie sua conta para começar' : 'Entre na sua conta'}
          </p>
        </div>

        {/* Form Card */}
        <div className="glass-card rounded-2xl p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {isSignUp && (
              <div>
                <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">
                  Nome Completo
                </label>
                <input
                  type="text"
                  name="fullName"
                  value={formData.fullName}
                  onChange={handleChange}
                  required={isSignUp}
                  placeholder="Seu nome"
                  className="w-full"
                  disabled={submitting}
                />
              </div>
            )}

            <div>
              <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">
                Email
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                placeholder="seu@email.com"
                className="w-full"
                disabled={submitting}
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider block mb-2">
                Senha
              </label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                required
                placeholder="••••••••"
                className="w-full"
                disabled={submitting}
                minLength={6}
              />
              {isSignUp && (
                <p className="text-xs text-on-surface-variant mt-1">
                  Mínimo de 6 caracteres
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="btn-primary w-full justify-center disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                  {isSignUp ? 'Criando conta...' : 'Entrando...'}
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-lg">
                    {isSignUp ? 'person_add' : 'login'}
                  </span>
                  {isSignUp ? 'Criar Conta' : 'Entrar'}
                </>
              )}
            </button>
          </form>

          {/* Toggle Sign Up / Sign In */}
          <div className="mt-6 pt-6 border-t border-outline-variant/10 text-center">
            <button
              onClick={() => setIsSignUp(!isSignUp)}
              className="text-sm text-primary hover:underline"
              disabled={submitting}
            >
              {isSignUp
                ? 'Já tem uma conta? Entre aqui'
                : 'Não tem conta? Crie uma agora'}
            </button>
          </div>
        </div>

        {/* Info Card */}
        <div className="mt-6 glass-card rounded-lg p-4">
          <div className="flex gap-3">
            <span className="material-symbols-outlined text-primary text-xl">info</span>
            <div className="flex-1">
              <p className="text-sm text-on-surface-variant leading-relaxed">
                Cada usuário tem seus próprios leads, tarefas e configurações.
                Os conjuntos de locais são compartilhados entre todos os usuários.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
