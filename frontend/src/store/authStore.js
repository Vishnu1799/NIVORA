import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from '../lib/api'

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: async (email, password) => {
        const { data } = await api.post('/auth/login', { email, password })
        localStorage.setItem('nivora_token', data.access_token)
        set({ user: { id: data.user_id, name: data.name, role: data.role }, token: data.access_token, isAuthenticated: true })
        return data
      },

      register: async (name, email, password, role = 'CUSTOMER') => {
        const { data } = await api.post('/auth/register', { name, email, password, role })
        localStorage.setItem('nivora_token', data.access_token)
        set({ user: { id: data.user_id, name: data.name, role: data.role }, token: data.access_token, isAuthenticated: true })
        return data
      },

      logout: () => {
        localStorage.removeItem('nivora_token')
        set({ user: null, token: null, isAuthenticated: false })
      },
    }),
    { name: 'nivora-auth', partialize: (state) => ({ user: state.user, token: state.token, isAuthenticated: state.isAuthenticated }) }
  )
)
