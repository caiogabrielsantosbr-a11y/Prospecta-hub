/**
 * AuthContext - Manages user authentication state and operations
 */
import { createContext, useContext, useState, useEffect } from 'react'
import { supabase } from '../config/supabase'
import toast from 'react-hot-toast'

const AuthContext = createContext({})

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check active session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null)
      if (session?.user) {
        loadProfile(session.user.id)
      } else {
        setLoading(false)
      }
    })

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      console.log('Auth event:', event)
      
      if (event === 'SIGNED_IN') {
        toast.success('Login realizado com sucesso!')
      }
      
      if (event === 'USER_UPDATED') {
        toast.success('Email confirmado com sucesso!')
      }
      
      setUser(session?.user ?? null)
      if (session?.user) {
        loadProfile(session.user.id)
      } else {
        setProfile(null)
        setLoading(false)
      }
    })

    return () => subscription.unsubscribe()
  }, [])

  const loadProfile = async (userId) => {
    try {
      const { data, error } = await supabase
        .from('users')
        .select('*')
        .eq('id', userId)
        .single()

      if (error) throw error
      setProfile(data)
    } catch (error) {
      console.error('Error loading profile:', error)
    } finally {
      setLoading(false)
    }
  }

  const signUp = async (email, password, fullName) => {
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: fullName
          },
          emailRedirectTo: `${window.location.origin}/`
        }
      })

      if (error) throw error
      
      // Check if email confirmation is required
      if (data?.user && !data.session) {
        toast.success('Conta criada! Verifique seu email para confirmar.')
      } else {
        toast.success('Conta criada com sucesso!')
      }
      
      return { data, error: null }
    } catch (error) {
      console.error('Error signing up:', error)
      toast.error(error.message || 'Erro ao criar conta')
      return { data: null, error }
    }
  }

  const signIn = async (email, password) => {
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
      })

      if (error) throw error
      
      toast.success('Login realizado com sucesso!')
      return { data, error: null }
    } catch (error) {
      console.error('Error signing in:', error)
      toast.error(error.message || 'Erro ao fazer login')
      return { data: null, error }
    }
  }

  const signOut = async () => {
    try {
      const { error } = await supabase.auth.signOut()
      if (error) throw error
      
      toast.success('Logout realizado com sucesso!')
    } catch (error) {
      console.error('Error signing out:', error)
      toast.error('Erro ao fazer logout')
    }
  }

  const updateProfile = async (updates) => {
    try {
      const { data, error } = await supabase
        .from('users')
        .update(updates)
        .eq('id', user.id)
        .select()
        .single()

      if (error) throw error
      
      setProfile(data)
      toast.success('Perfil atualizado com sucesso!')
      return { data, error: null }
    } catch (error) {
      console.error('Error updating profile:', error)
      toast.error('Erro ao atualizar perfil')
      return { data: null, error }
    }
  }

  const uploadAvatar = async (file) => {
    try {
      const fileExt = file.name.split('.').pop()
      const fileName = `${user.id}-${Math.random()}.${fileExt}`
      const filePath = `avatars/${fileName}`

      const { error: uploadError } = await supabase.storage
        .from('avatars')
        .upload(filePath, file)

      if (uploadError) throw uploadError

      const { data: { publicUrl } } = supabase.storage
        .from('avatars')
        .getPublicUrl(filePath)

      await updateProfile({ avatar_url: publicUrl })
      
      return { url: publicUrl, error: null }
    } catch (error) {
      console.error('Error uploading avatar:', error)
      toast.error('Erro ao fazer upload da foto')
      return { url: null, error }
    }
  }

  const value = {
    user,
    profile,
    loading,
    signUp,
    signIn,
    signOut,
    updateProfile,
    uploadAvatar,
    loadProfile
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
