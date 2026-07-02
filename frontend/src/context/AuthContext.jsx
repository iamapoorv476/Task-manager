import { createContext, useContext, useEffect, useState } from 'react'
import client, { clearToken, getToken, setToken } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  // Starts true and stays true until we've resolved whether an existing
  // token (from a previous session) is still valid -- without this,
  // ProtectedRoute would redirect to /login for a split second on every
  // page refresh, even for someone who's actually still logged in.
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = getToken()
    if (!token) {
      setLoading(false)
      return
    }
    client
      .get('/users/me')
      .then((res) => setUser(res.data.data))
      .catch(() => clearToken())
      .finally(() => setLoading(false))
  }, [])

  async function login(email, password) {
    const form = new URLSearchParams()
    form.set('username', email)
    form.set('password', password)
    const res = await client.post('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    setToken(res.data.data.access_token)
    const me = await client.get('/users/me')
    setUser(me.data.data)
  }

  async function register(name, email, password) {
    await client.post('/auth/register', { name, email, password })
    // Registration doesn't log you in automatically on the backend --
    // it's a separate account-creation step, so the frontend follows
    // that same shape rather than quietly logging in behind the scenes.
    await login(email, password)
  }

  function logout() {
    clearToken()
    setUser(null)
  }

  const value = {
    user,
    loading,
    isAuthenticated: Boolean(user),
    isAdmin: user?.role === 'ADMIN',
    login,
    register,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return ctx
}
