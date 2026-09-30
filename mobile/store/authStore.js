import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from '../lib/api';

export const useAuthStore = create((set) => ({
  user: null,
  isAuthenticated: false,
  initialized: false,

  init: async () => {
    try {
      const token = await AsyncStorage.getItem('nivora_token');
      const userStr = await AsyncStorage.getItem('nivora_user');
      if (token && userStr) {
        set({ user: JSON.parse(userStr), isAuthenticated: true });
      }
    } catch (e) {}
    set({ initialized: true });
  },

  login: async (email, password) => {
    const { data } = await api.post('/auth/login', { email, password });
    const user = { id: data.user_id, name: data.name, role: data.role };
    await AsyncStorage.setItem('nivora_token', data.access_token);
    await AsyncStorage.setItem('nivora_user', JSON.stringify(user));
    set({ user, isAuthenticated: true });
    return data;
  },

  register: async (name, email, password, role = 'CUSTOMER') => {
    const { data } = await api.post('/auth/register', { name, email, password, role });
    const user = { id: data.user_id, name: data.name, role: data.role };
    await AsyncStorage.setItem('nivora_token', data.access_token);
    await AsyncStorage.setItem('nivora_user', JSON.stringify(user));
    set({ user, isAuthenticated: true });
    return data;
  },

  logout: async () => {
    await AsyncStorage.removeItem('nivora_token');
    await AsyncStorage.removeItem('nivora_user');
    set({ user: null, isAuthenticated: false });
  },
}));
