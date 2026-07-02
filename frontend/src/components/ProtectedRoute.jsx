import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    // Deliberately blank-but-brief rather than a spinner -- this only
    // shows for the moment it takes to check an existing token against
    // /users/me on first load, which is fast enough that a spinner
    // would just flash and add noise.
    return null
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return children
}
