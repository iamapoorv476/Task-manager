import axios from 'axios'

// Token lives in localStorage, not just React state -- that's what
// keeps someone logged in across a page refresh. The real tradeoff:
// localStorage is readable by any JS running on the page, so an XSS
// vulnerability elsewhere in the app could steal the token. The more
// locked-down alternative is an httpOnly cookie set by the server,
// which JS can't read at all -- but that needs the backend to issue
// and manage cookies (plus CSRF protection alongside it), which isn't
// what this API does; it hands back a bearer token in the JSON body.
// Given that, localStorage is the standard, honest choice for a bearer
// token SPA at this scope, not a shortcut I'm pretending isn't a tradeoff.
const TOKEN_KEY = 'task_manager_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

const client = axios.create({
  baseURL: '/api/v1',
})

// Request interceptor: attach the token to every outgoing request. This
// is the whole point of centralizing this in one client instead of
// passing headers manually at every call site -- one place to get it
// right, everywhere benefits.
client.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: a 401 means the token is missing, invalid, or
// expired -- in every one of those cases the right move is the same:
// clear it and send the person back to log in. Handling that here means
// no individual page has to remember to do this itself.
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearToken()
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default client
