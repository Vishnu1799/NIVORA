import { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, SafeAreaView, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useAuthStore } from '../../store/authStore';
import { COLORS, SHADOWS, RADIUS } from '../../constants/theme';
import api from '../../lib/api';

const TABS = ['All', 'Delivered', 'Cancelled'];

export default function OrdersScreen() {
  const { isAuthenticated } = useAuthStore();
  const router = useRouter();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('All');

  useEffect(() => {
    if (!isAuthenticated) { setLoading(false); return; }
    api.get('/orders').then(({ data }) => setOrders(data)).catch(() => {}).finally(() => setLoading(false));
  }, [isAuthenticated]);

  if (!isAuthenticated) return (
    <SafeAreaView style={{ flex: 1, backgroundColor: COLORS.background, alignItems: 'center', justifyContent: 'center', padding: 32 }}>
      <Ionicons name="receipt-outline" size={64} color="#E5E7EB" />
      <Text style={{ fontSize: 18, fontWeight: '700', color: COLORS.textSecondary, marginTop: 16, marginBottom: 20 }}>Sign in to see your orders</Text>
      <TouchableOpacity onPress={() => router.push('/auth/login')} style={{ backgroundColor: COLORS.primary, paddingHorizontal: 32, paddingVertical: 14, borderRadius: RADIUS.md }}>
        <Text style={{ color: 'white', fontWeight: '700', fontSize: 15 }}>Sign In</Text>
      </TouchableOpacity>
    </SafeAreaView>
  );

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: COLORS.background }}>
      <View style={{ backgroundColor: COLORS.white, paddingHorizontal: 16, paddingTop: 16, paddingBottom: 12 }}>
        <Text style={{ fontSize: 20, fontWeight: '800', color: COLORS.textPrimary, marginBottom: 12 }}>Order History</Text>
        <View style={{ flexDirection: 'row', gap: 8 }}>
          {TABS.map((t) => (
            <TouchableOpacity
              key={t}
              onPress={() => setTab(t)}
              style={{
                paddingHorizontal: 16, paddingVertical: 7, borderRadius: 20,
                backgroundColor: tab === t ? COLORS.primary : COLORS.white,
                borderWidth: 1, borderColor: tab === t ? COLORS.primary : COLORS.border,
              }}
            >
              <Text style={{ fontWeight: '600', fontSize: 13, color: tab === t ? 'white' : COLORS.textSecondary }}>{t}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {loading ? (
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
          <ActivityIndicator color={COLORS.primary} size="large" />
        </View>
      ) : (
        <FlatList
          data={orders}
          keyExtractor={(item) => item.id}
          contentContainerStyle={{ padding: 16, gap: 12 }}
          ListEmptyComponent={
            <View style={{ alignItems: 'center', paddingTop: 60 }}>
              <Ionicons name="receipt-outline" size={64} color="#E5E7EB" />
              <Text style={{ color: COLORS.textLight, fontSize: 15, marginTop: 12 }}>No orders yet</Text>
            </View>
          }
          renderItem={({ item: order }) => (
            <View style={{ backgroundColor: COLORS.white, borderRadius: RADIUS.md, padding: 14, ...SHADOWS.small }}>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 }}>
                <View>
                  <Text style={{ fontWeight: '700', color: COLORS.textPrimary, fontSize: 14 }}>#{order.id.slice(-8).toUpperCase()}</Text>
                  <Text style={{ color: COLORS.textLight, fontSize: 12, marginTop: 2 }}>{order.created_at ? new Date(order.created_at).toLocaleDateString() : ''}</Text>
                </View>
                <View style={{ backgroundColor: COLORS.primaryLight, paddingHorizontal: 10, paddingVertical: 4, borderRadius: 20 }}>
                  <Text style={{ color: COLORS.primary, fontWeight: '700', fontSize: 12 }}>{order.status}</Text>
                </View>
              </View>
              <View style={{ height: 1, backgroundColor: COLORS.border, marginVertical: 8 }} />
              {order.items?.slice(0, 2).map((item, i) => (
                <Text key={i} style={{ color: COLORS.textSecondary, fontSize: 13, paddingVertical: 2 }}>{item.product_name} × {item.quantity}</Text>
              ))}
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 8 }}>
                <Text style={{ color: COLORS.textSecondary, fontSize: 13 }}>Total</Text>
                <Text style={{ fontWeight: '800', color: COLORS.textPrimary, fontSize: 15 }}>₹{order.total_amount?.toFixed(0)}</Text>
              </View>
            </View>
          )}
        />
      )}
    </SafeAreaView>
  );
}
