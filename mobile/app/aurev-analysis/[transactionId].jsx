import { useEffect, useState, useRef } from 'react';
import { View, Text, SafeAreaView, ScrollView, TouchableOpacity, Animated, Easing } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import api from '../../lib/api';

const DARK = '#0B1F12';
const DARK_CARD = '#122B1A';
const GREEN = '#22C55E';
const GREEN_DIM = '#166534';

const CHECK_ITEMS = [
  { key: 'gateway', label: 'Gateway response', detail: 'Timeout (no final status)' },
  { key: 'order', label: 'Order status', detail: 'Pending' },
  { key: 'attempts', label: 'Previous attempts', detail: '0' },
  { key: 'risk', label: 'Risk check', detail: 'Low risk' },
  { key: 'recovery', label: 'Recovery rules', detail: 'Safe to retry' },
];

export default function AurevAnalysisScreen() {
  const { transactionId } = useLocalSearchParams();
  const router = useRouter();
  const [payment, setPayment] = useState(null);
  const [visibleItems, setVisibleItems] = useState(0);
  const [analyzing, setAnalyzing] = useState(true);
  const progressAnim = useRef(new Animated.Value(0)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    api.get(`/payments/${transactionId}/status`).then(({ data }) => setPayment(data)).catch(() => {});

    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1.08, duration: 1000, useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1, duration: 1000, useNativeDriver: true }),
      ])
    ).start();

    let count = 0;
    const interval = setInterval(() => {
      count++;
      setVisibleItems(count);
      if (count >= CHECK_ITEMS.length) {
        clearInterval(interval);
        Animated.timing(progressAnim, { toValue: 1, duration: 1500, useNativeDriver: false }).start(() => {
          setAnalyzing(false);
          setTimeout(() => router.replace(`/payment-result/${transactionId}`), 1000);
        });
      }
    }, 700);

    return () => clearInterval(interval);
  }, [transactionId]);

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: DARK }}>
      <ScrollView contentContainerStyle={{ padding: 24, paddingBottom: 40 }}>
        {/* Header */}
        <View style={{ alignItems: 'center', marginBottom: 32, marginTop: 16 }}>
          <Animated.View style={[
            { transform: [{ scale: pulseAnim }] },
            { width: 80, height: 80, borderRadius: 40, backgroundColor: DARK_CARD, borderWidth: 2, borderColor: GREEN_DIM, alignItems: 'center', justifyContent: 'center', marginBottom: 16 },
            { shadowColor: GREEN, shadowOpacity: 0.4, shadowRadius: 20, elevation: 10 },
          ]}>
            <Ionicons name="hardware-chip" size={44} color={GREEN} />
          </Animated.View>
          <Text style={{ fontSize: 20, fontWeight: '800', color: '#FFFFFF', letterSpacing: -0.5 }}>AUREV AI</Text>
          <Text style={{ color: '#6EE7B7', fontSize: 13, marginTop: 4 }}>Payment Recovery Agent</Text>
        </View>

        {/* Analyzing card */}
        <View style={{ backgroundColor: DARK_CARD, borderRadius: 16, padding: 18, borderWidth: 1, borderColor: '#1E3A28' }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <Ionicons name="time-outline" size={18} color={GREEN} />
            <Text style={{ color: '#FFFFFF', fontWeight: '700', fontSize: 15 }}>Analyzing payment...</Text>
          </View>
          <Text style={{ color: '#9CA3AF', fontSize: 13, marginBottom: 20, lineHeight: 18 }}>
            Checking gateway status, order details,{"\n"}previous attempts and risk signals.
          </Text>

          {/* Checklist items */}
          <View style={{ gap: 14 }}>
            {CHECK_ITEMS.map((item, i) => {
              const isVisible = i < visibleItems;
              return (
                <View key={item.key} style={{ flexDirection: 'row', alignItems: 'center', gap: 12, opacity: isVisible ? 1 : 0.25 }}>
                  <View style={{
                    width: 24, height: 24, borderRadius: 12,
                    backgroundColor: isVisible ? GREEN : '#1E3A28',
                    borderWidth: isVisible ? 0 : 1, borderColor: '#2D5234',
                    alignItems: 'center', justifyContent: 'center',
                  }}>
                    {isVisible && <Ionicons name="checkmark" size={14} color="white" />}
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={{ color: '#FFFFFF', fontWeight: '600', fontSize: 14 }}>{item.label}</Text>
                    <Text style={{ color: '#6B7280', fontSize: 12, marginTop: 1 }}>{item.detail}</Text>
                  </View>
                </View>
              );
            })}
          </View>

          {/* Progress bar */}
          {visibleItems >= CHECK_ITEMS.length && (
            <View style={{ marginTop: 20 }}>
              <View style={{ height: 4, backgroundColor: '#1E3A28', borderRadius: 2, overflow: 'hidden' }}>
                <Animated.View style={[
                  { height: '100%', borderRadius: 2, backgroundColor: GREEN },
                  { width: progressAnim.interpolate({ inputRange: [0, 1], outputRange: ['0%', '100%'] }) },
                ]} />
              </View>
              <Text style={{ color: '#6EE7B7', fontSize: 12, marginTop: 8 }}>
                {analyzing ? 'Evaluating next best action...' : '✓ Analysis complete'}
              </Text>
            </View>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}
