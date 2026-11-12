import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  user_id: string
  name: string
  role: string
  access_token: string
}

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  setUser: (user: User) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      setUser: (user) => {
        localStorage.setItem('access_token', user.access_token)
        set({ user, isAuthenticated: true })
      },
      logout: () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('user')
        set({ user: null, isAuthenticated: false })
      },
    }),
    {
      name: 'auth-store',
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
)
