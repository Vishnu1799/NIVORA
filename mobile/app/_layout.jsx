import { useEffect } from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useAuthStore } from '../store/authStore';

export default function RootLayout() {
  const init = useAuthStore((s) => s.init);
  useEffect(() => { init(); }, []);
  return (
    <>
      <StatusBar style="dark" backgroundColor="#FFFFFF" />
      <Stack screenOptions={{ headerShown: false, animation: 'slide_from_right' }}>
        <Stack.Screen name="index" />
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="auth/login" />
        <Stack.Screen name="auth/register" />
        <Stack.Screen name="product/[id]" />
        <Stack.Screen name="category/[id]" />
        <Stack.Screen name="checkout" />
        <Stack.Screen name="payment/[transactionId]" />
        <Stack.Screen name="payment-result/[transactionId]" />
        <Stack.Screen name="aurev-analysis/[transactionId]" />
        <Stack.Screen name="aurev-dashboard" />
      </Stack>
    </>
  );
}
