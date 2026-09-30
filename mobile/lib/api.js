import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

// For physical device on the same WiFi/Hotspot network:
const DEV_IP = '192.168.137.32';

// Auto-select host: web uses localhost, physical phone / simulator uses local LAN IP
const HOST = Platform.OS === 'web' ? 'localhost' : DEV_IP;

export const BASE_URL = `http://${HOST}:8000`;
export const WS_BASE = `ws://${HOST}:8000`;
export const BANK_URL = `http://${HOST}:8001`;

const api = axios.create({
  baseURL: `${BASE_URL}/api`,
  timeout: 30000,
});

api.interceptors.request.use(async (config) => {
  try {
    const token = await AsyncStorage.getItem('nivora_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
  } catch (e) {}
  return config;
});

export default api;
