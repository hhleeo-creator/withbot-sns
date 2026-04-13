import { createContext, useContext, useState, useEffect } from 'react'
import { authAPI } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('withbot_token')
    if (token) {
      authAPI.me()
        .then(res => setUser(res.data))
        .catch(() => {
          localStorage.removeItem('withbot_token')
          localStorage.removeItem('withbot_user')
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (googleToken) => {
    const res = await authAPI.login(googleToken)
    const { session_token, ...userData } = res.data
    localStorage.setItem('withbot_token', session_token)
    localStorage.setItem('withbot_user', JSON.stringify(userData))
    setUser(userData)
    return userData
  }

  const logout = () => {
    authAPI.logout().catch(() => {})
    localStorage.removeItem('withbot_token')
    localStorage.removeItem('withbot_user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
