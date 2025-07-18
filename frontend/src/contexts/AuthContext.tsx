import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { authApi } from '../services/api'

interface User {
  id: number
  username: string
  role_name: string
  status: string
  last_login_time?: string
  created_at: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check for stored token on app start
    const storedToken = localStorage.getItem('token')
    if (storedToken) {
      setToken(storedToken)
      // Verify token and get user info
      authApi.getCurrentUser()
        .then(userData => {
          setUser(userData)
        })
        .catch(() => {
          // Token is invalid, remove it
          localStorage.removeItem('token')
          setToken(null)
        })
        .finally(() => {
          setLoading(false)
        })
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (username: string, password: string) => {
    try {
      const response = await authApi.login(username, password)
      const { access_token, user: userData } = response
      
      setToken(access_token)
      setUser(userData)
      localStorage.setItem('token', access_token)
    } catch (error) {
      throw error
    }
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem('token')
  }

  const value = {
    user,
    token,
    loading,
    login,
    logout
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}