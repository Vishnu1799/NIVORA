import { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, SafeAreaView, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useCartStore } from '../store/cartStore';
import { useAuthStore } from '../store/authStore';
import { COLORS, SHADOWS, RADIUS } from '../constants/theme';
import api from '../lib/api';

const PAYMENT_METHODS = [
  { value: 'UPI', label: 'UPI', desc: 'Google Pay, PhonePe, Paytm', icon: 'phone-portrait-outline' },
  { value: 'CARD', label: 'Credit / Debit Card', desc: 'Visa, Mastercard, RuPay', icon: 'card-outline' },
  { value: 'NET_BANKING', label: 'Net Banking', desc: 'All major banks', icon: 'business-outline' },
  { value: 'WALLET', label: 'Wallet', desc: 'Paytm, Amazon Pay', icon: 'wallet-outline' },
  { value: 'COD', label: 'Cash on Delivery', desc: 'Pay when delivered', icon: 'cash-outline' },
];

export default function CheckoutScreen() {
  const { items, getTotal, clearCart } = useCartStore();
  const { user } = useAuthStore();
  const router = useRouter();
  const [selectedMethod, setSelectedMethod] = useState('UPI');
  const [loading, setLoading] = useState(false);
  const total = getTotal();
  const DELIVERY = 20;

  const handlePayNow = async () => {
    if (selectedMethod === 'COD') { router.push('/payment-result/DEMO_COD'); return; }
    setLoading(true);
    try {
      const { data: order } = await api.post('/orders', {
        items: items.map((i) => ({ product_id: i.id, quantity: i.qty })),
        delivery_address: { city: 'Bengaluru', state: 'Karnataka', pincode: '560034' },
      });
      const idempotencyKey = `${order.id}_${Date.now()}`;
      const { data: payment } = await api.post('/payments', {
        order_id: order.id,
        amount: total + DELIVERY,
        payment_method: selectedMethod,
        idempotency_key: idempotencyKey,
      });
      clearCart();
      router.push(`/payment/${payment.transaction_id}`);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to initiate payment');
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: COLORS.background }}>
      {/* Header */}
      <View style={{ backgroundColor: COLORS.white, paddingHorizontal: 16, paddingTop: 12, paddingBottom: 12, flexDirection: 'row', alignItems: 'center', gap: 12, borderBottomWidth: 1, borderBottomColor: COLORS.border }}>
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={COLORS.textPrimary} />
        </TouchableOpacity>
        <Text style={{ fontSize: 18, fontWeight: '700', color: COLORS.textPrimary }}>Payment</Text>
      </View>

      <ScrollView contentContainerStyle={{ padding: 16, gap: 14 }}>
        {/* Delivery address */}
        <View style={{ backgroundColor: COLORS.white, borderRadius: RADIUS.md, padding: 14, ...SHADOWS.small }}>
          <Text style={{ fontWeight: '700', color: COLORS.textPrimary, fontSize: 15, marginBottom: 10 }}>Delivery Address</Text>
          <View style={{ flexDirection: 'row', alignItems: 'flex-start', gap: 10 }}>
            <Ionicons name="location" size={20} color={COLORS.primary} style={{ marginTop: 2 }} />
            <View style={{ flex: 1 }}>
              <Text style={{ fontWeight: '700', color: COLORS.textPrimary }}>Home</Text>
              <Text style={{ color: COLORS.textSecondary, fontSize: 13, marginTop: 2, lineHeight: 18 }}>12, Green Park, 3rd Cross,{"\n"}Koramangala, Bangalore - 560034</Text>
            </View>
            <TouchableOpacity><Text style={{ color: COLORS.primary, fontWeight: '600', fontSize: 13 }}>Change</Text></TouchableOpacity>
          </View>
        </View>

        {/* Payment method */}
        <View style={{ backgroundColor: COLORS.white, borderRadius: RADIUS.md, padding: 14, ...SHADOWS.small }}>
          <Text style={{ fontWeight: '700', color: COLORS.textPrimary, fontSize: 15, marginBottom: 12 }}>Payment Method</Text>
          <View style={{ gap: 0 }}>
            {PAYMENT_METHODS.map((method, i) => (
              <TouchableOpacity
                key={method.value}
                onPress={() => setSelectedMethod(method.value)}
                style={{
                  flexDirection: 'row', alignItems: 'center', gap: 12,
                  paddingVertical: 13,
                  borderBottomWidth: i < PAYMENT_METHODS.length - 1 ? 1 : 0,
                  borderBottomColor: COLORS.border,
                }}
              >
                {/* Radio button */}
                <View style={{
                  width: 20, height: 20, borderRadius: 10,
                  borderWidth: 2, borderColor: selectedMethod === method.value ? COLORS.primary : COLORS.border,
                  alignItems: 'center', justifyContent: 'center',
                }}>
                  {selectedMethod === method.value && (
                    <View style={{ width: 10, height: 10, borderRadius: 5, backgroundColor: COLORS.primary }} />
                  )}
                </View>
                <Ionicons name={method.icon} size={22} color={selectedMethod === method.value ? COLORS.primary : COLORS.textSecondary} />
                <View style={{ flex: 1 }}>
                  <Text style={{ fontWeight: selectedMethod === method.value ? '700' : '500', color: COLORS.textPrimary, fontSize: 14 }}>
                    {method.value === 'UPI' ? '⚡ ' : ''}{method.label}
                  </Text>
                  <Text style={{ color: COLORS.textLight, fontSize: 11, marginTop: 1 }}>{method.desc}</Text>
                </View>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Order summary */}
        <View style={{ backgroundColor: COLORS.white, borderRadius: RADIUS.md, padding: 14, ...SHADOWS.small }}>
          <Text style={{ fontWeight: '700', color: COLORS.textPrimary, fontSize: 15, marginBottom: 10 }}>Order Summary</Text>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 4 }}>
            <Text style={{ color: COLORS.textSecondary, fontSize: 14 }}>Order Value</Text>
            <Text style={{ fontWeight: '600', fontSize: 14, color: COLORS.textPrimary }}>₹{total.toFixed(0)}</Text>
          </View>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 4 }}>
            <Text style={{ color: COLORS.textSecondary, fontSize: 14 }}>Delivery Fee</Text>
            <Text style={{ fontWeight: '600', fontSize: 14, color: COLORS.textPrimary }}>₹{DELIVERY}</Text>
          </View>
          <View style={{ height: 1, backgroundColor: COLORS.border, marginVertical: 8 }} />
          <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
            <Text style={{ fontWeight: '700', fontSize: 15, color: COLORS.textPrimary }}>Total</Text>
            <Text style={{ fontWeight: '800', fontSize: 17, color: COLORS.textPrimary }}>₹{(total + DELIVERY).toFixed(0)}</Text>
          </View>
        </View>

        <TouchableOpacity
          onPress={handlePayNow}
          disabled={loading}
          style={{ backgroundColor: loading ? '#9CC4B2' : COLORS.primary, borderRadius: RADIUS.md, paddingVertical: 16, alignItems: 'center' }}
        >
          {loading ? <ActivityIndicator color="white" /> : <Text style={{ color: 'white', fontWeight: '700', fontSize: 16 }}>Pay Now</Text>}
        </TouchableOpacity>

        <Text style={{ color: COLORS.textLight, fontSize: 11, textAlign: 'center' }}>In case of multiple failures, your account may be temporarily blocked for security reasons.</Text>
      </ScrollView>
    </SafeAreaView>
  );
}
