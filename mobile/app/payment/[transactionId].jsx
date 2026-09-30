import { useEffect, useState, useRef } from 'react';
import { View, Text, SafeAreaView, Animated, Easing, TouchableOpacity } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../../constants/theme';
import api, { WS_BASE } from '../../lib/api';

const FINAL_STATES = ['SUCCESS', 'FAILED', 'DECLINED', 'ESCALATED', 'UNKNOWN'];

export default function PaymentProcessingScreen() {
  const { transactionId } = useLocalSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState('PROCESSING');
  const [amount, setAmount] = useState(null);
  const [paymentData, setPaymentData] = useState(null);
  const pollRef = useRef(null);
  const dots = [useRef(new Animated.Value(0.3)).current, useRef(new Animated.Value(0.3)).current, useRef(new Animated.Value(0.3)).current];

  useEffect(() => {
    // Animate loading dots
    dots.forEach((dot, i) => {
      Animated.loop(
        Animated.sequence([
          Animated.delay(i * 200),
          Animated.timing(dot, { toValue: 1, duration: 500, useNativeDriver: true, easing: Easing.ease }),
          Animated.timing(dot, { toValue: 0.3, duration: 500, useNativeDriver: true }),
        ])
      ).start();
    });

    // WebSocket
    try {
      const ws = new WebSocket(`${WS_BASE}/ws/payments/${transactionId}`);
      ws.onmessage = (e) => { const d = JSON.parse(e.data); };
    } catch (e) {}

    // Polling
    pollRef.current = setInterval(async () => {
      try {
        const { data } = await api.get(`/payments/${transactionId}/status`);
        setStatus(data.status);
        if (data.amount) setAmount(data.amount);
        setPaymentData(data);
        if (FINAL_STATES.includes(data.status)) {
          clearInterval(pollRef.current);
          if (data.status === 'FAILED') {
            setTimeout(() => router.replace(`/aurev-analysis/${transactionId}`), 800);
          } else {
            setTimeout(() => router.replace(`/payment-result/${transactionId}`), 1000);
          }
        }
      } catch (e) {}
    }, 2000);

    return () => clearInterval(pollRef.current);
  }, [transactionId]);

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: COLORS.white }}>
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', padding: 32 }}>
        <Ionicons name="leaf" size={40} color={COLORS.primary} />
        <Text style={{ fontSize: 28, fontWeight: '800', color: COLORS.primary, marginTop: 8 }}>Nivora</Text>

        {amount && (
          <Text style={{ fontSize: 44, fontWeight: '800', color: COLORS.textPrimary, marginTop: 40, marginBottom: 8 }}>₹{parseFloat(amount).toFixed(0)}</Text>
        )}

        <View style={{ alignItems: 'center', marginTop: amount ? 20 : 60 }}>
          {/* Animated dots */}
          <View style={{ flexDirection: 'row', gap: 10, marginBottom: 24 }}>
            {dots.map((dot, i) => (
              <Animated.View key={i} style={{ width: 12, height: 12, borderRadius: 6, backgroundColor: COLORS.primary, opacity: dot }} />
            ))}
          </View>
          <Text style={{ fontSize: 18, fontWeight: '600', color: COLORS.textPrimary, textAlign: 'center' }}>Processing payment...</Text>
          <Text style={{ color: COLORS.textSecondary, fontSize: 14, marginTop: 8, textAlign: 'center', lineHeight: 22 }}>
            AUREV AI is securely{"\n"}verifying your payment.
          </Text>
        </View>

        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, position: 'absolute', bottom: 48 }}>
          <Ionicons name="lock-closed" size={14} color={COLORS.textLight} />
          <Text style={{ color: COLORS.textLight, fontSize: 13 }}>Protected by AUREV AI</Text>
        </View>
      </View>
    </SafeAreaView>
  );
}
