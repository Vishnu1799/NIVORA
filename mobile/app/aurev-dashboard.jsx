import { useState, useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, SafeAreaView, ActivityIndicator, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import api, { BANK_URL } from '../lib/api';
import { COLORS, SHADOWS, RADIUS } from '../constants/theme';

const SCENARIOS = [
  { key: 'UP', label: 'Normal', color: COLORS.primary, payload: { state: 'UP', failure_rate: 0 } },
  { key: 'DOWN', label: 'Bank Down', color: '#EF4444', payload: { state: 'DOWN' } },
  { key: 'TIMEOUT', label: 'Timeout', color: '#F59E0B', payload: { state: 'UP', force_outcome: 'TIMEOUT' } },
  { key: 'UNKNOWN', label: 'Unknown', color: '#8B5CF6', payload: { state: 'UP', force_outcome: 'UNKNOWN' } },
  { key: 'DEGRADED', label: 'Degraded', color: '#EC4899', payload: { state: 'DEGRADED', failure_rate: 0.7, response_delay_ms: 3000 } },
];

export default function AurevDashboardScreen() {
  const router = useRouter();
  const [metrics, setMetrics] = useState(null);
  const [events, setEvents] = useState([]);
  const [scenario, setScenario] = useState('UP');

  useEffect(() => {
    const fetch = async () => {
      try {
        const [{ data: m }, { data: e }] = await Promise.all([api.get('/aurev/metrics'), api.get('/aurev/events')]);
        setMetrics(m);
        setEvents(e.slice(0, 20));
      } catch (e) {}
    };
    fetch();
    const i = setInterval(fetch, 3000);
    return () => clearInterval(i);
  }, []);

  const setBank = async (s) => {
    try {
      await fetch(`${BANK_URL}/admin/service-state`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(s.payload) });
      setScenario(s.key);
    } catch (e) {
      Alert.alert('Error', 'Cannot connect to bank simulator on port 8001');
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: COLORS.background }}>
      <View style={{ backgroundColor: COLORS.white, paddingHorizontal: 16, paddingTop: 12, paddingBottom: 12, flexDirection: 'row', alignItems: 'center', gap: 10, borderBottomWidth: 1, borderBottomColor: COLORS.border }}>
        <TouchableOpacity onPress={() => router.back()}><Ionicons name="arrow-back" size={24} color={COLORS.textPrimary} /></TouchableOpacity>
        <Ionicons name="hardware-chip" size={22} color={COLORS.primary} />
        <Text style={{ fontSize: 17, fontWeight: '700', color: COLORS.textPrimary }}>AUREV AI Dashboard</Text>
      </View>

      <ScrollView contentContainerStyle={{ padding: 16, gap: 14 }}>
        {/* Demo controls */}
        <View style={{ backgroundColor: COLORS.white, borderRadius: RADIUS.md, padding: 14, ...SHADOWS.small }}>
          <Text style={{ fontWeight: '700', color: COLORS.textPrimary, marginBottom: 4 }}>🎮 Demo Controls</Text>
          <Text style={{ color: COLORS.textSecondary, fontSize: 12, marginBottom: 12 }}>Set bank state to demonstrate AUREV AI recovery</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View style={{ flexDirection: 'row', gap: 8 }}>
              {SCENARIOS.map((s) => (
                <TouchableOpacity key={s.key} onPress={() => setBank(s)}
                  style={{ paddingHorizontal: 16, paddingVertical: 10, borderRadius: 20, backgroundColor: scenario === s.key ? s.color : '#F5F7FA', borderWidth: 1, borderColor: scenario === s.key ? s.color : COLORS.border }}
                >
                  <Text style={{ fontWeight: '700', fontSize: 13, color: scenario === s.key ? 'white' : COLORS.textSecondary }}>{s.label}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </ScrollView>
        </View>

        {/* Metrics */}
        {metrics ? (
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 10 }}>
            {[
              { label: 'Bank', value: metrics.bank_status, icon: 'wifi', color: metrics.bank_status === 'UP' ? COLORS.primary : '#EF4444' },
              { label: 'Recovered', value: metrics.auto_recovered, icon: 'shield-checkmark', color: COLORS.primary },
              { label: 'Escalated', value: metrics.escalated, icon: 'warning', color: '#F59E0B' },
              { label: 'Declined', value: metrics.declined, icon: 'close-circle', color: '#EF4444' },
            ].map((m) => (
              <View key={m.label} style={{ backgroundColor: COLORS.white, borderRadius: RADIUS.md, padding: 14, width: '47%', ...SHADOWS.small, alignItems: 'center' }}>
                <Ionicons name={m.icon} size={24} color={m.color} style={{ marginBottom: 6 }} />
                <Text style={{ fontSize: 20, fontWeight: '800', color: COLORS.textPrimary }}>{m.value ?? 0}</Text>
                <Text style={{ color: COLORS.textSecondary, fontSize: 12, marginTop: 2 }}>{m.label}</Text>
              </View>
            ))}
          </View>
        ) : <ActivityIndicator color={COLORS.primary} />}

        {/* Events */}
        <View style={{ backgroundColor: COLORS.white, borderRadius: RADIUS.md, padding: 14, ...SHADOWS.small }}>
          <Text style={{ fontWeight: '700', color: COLORS.textPrimary, fontSize: 15, marginBottom: 12 }}>Live Activity</Text>
          {events.length === 0 ? <Text style={{ color: COLORS.textLight, textAlign: 'center', paddingVertical: 20 }}>No activity yet. Make a payment to see AUREV AI in action.</Text> :
            events.map((e, i) => (
              <View key={i} style={{ flexDirection: 'row', gap: 10, paddingVertical: 8, borderBottomWidth: i < events.length - 1 ? 1 : 0, borderBottomColor: COLORS.border }}>
                <Text style={{ color: COLORS.textLight, fontSize: 11, width: 55 }}>{e.created_at ? new Date(e.created_at).toLocaleTimeString('en', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '--'}</Text>
                <Text style={{ flex: 1, fontSize: 13, color: e.event_type?.includes('recovered') || e.event_type?.includes('succeeded') ? COLORS.primary : e.event_type?.includes('failed') || e.event_type?.includes('escalated') ? '#EF4444' : COLORS.textPrimary }} numberOfLines={2}>{e.message || e.event_type}</Text>
              </View>
            ))
          }
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}
