import { useEffect, useState } from 'react';
import { View, Text, SafeAreaView, TouchableOpacity, ScrollView, ActivityIndicator } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import api from '../../lib/api';
import { COLORS, SHADOWS, RADIUS } from '../../constants/theme';

export default function PaymentResultScreen() {
  const { transactionId } = useLocalSearchParams();
  const router = useRouter();
  const [payment, setPayment] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (transactionId === 'DEMO_COD') {
      setPayment({ status: 'SUCCESS', transaction_id: 'DEMO_COD', amount: 0 });
      setLoading(false);
      return;
    }
    api.get(`/payments/${transactionId}/status`).then(({ data }) => setPayment(data)).finally(() => setLoading(false));
  }, [transactionId]);

  if (loading) return <SafeAreaView style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: COLORS.white }}><ActivityIndicator size="large" color={COLORS.primary} /></SafeAreaView>;
  if (!payment) return <SafeAreaView style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}><Text>Not found</Text></SafeAreaView>;

  const isSuccess = payment.status === 'SUCCESS';
  const isDeclined = payment.status === 'DECLINED';
  const isEscalated = payment.status === 'ESCALATED';
  const wasRecovered = isSuccess && (payment.recovery_attempt_count || 0) > 0;

  const getContent = () => {
    if (wasRecovered) return { icon: 'shield-checkmark', iconBg: '#DCFCE7', iconColor: COLORS.primary, title: 'Payment Recovered!', subtitle: 'AUREV AI successfully recovered your payment.', showAurev: true };
    if (isSuccess) return { icon: 'checkmark-circle', iconBg: '#DCFCE7', iconColor: COLORS.primary, title: 'Order Placed Successfully!', subtitle: 'Your groceries will be delivered soon.', showAurev: false };
    if (isDeclined) return { icon: 'close-circle', iconBg: '#FEE2E2', iconColor: COLORS.error, title: 'Payment Failed', subtitle: payment.failure_reason || "We couldn't complete your payment due to a timeout from the bank. Your order is not placed yet.", showAurev: false };
    if (isEscalated) return { icon: 'alert-circle', iconBg: '#FFF7ED', iconColor: '#F59E0B', title: 'Payment Under Review', subtitle: "We couldn't complete your payment safely. No additional payment attempt was made.", showAurev: true };
    return { icon: 'close-circle', iconBg: '#FEE2E2', iconColor: COLORS.error, title: 'Payment Failed', subtitle: 'Please try again.', showAurev: false };
  };

  const c = getContent();
  const orderNum = `#NV${Date.now().toString().slice(-7)}`;

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: COLORS.background }}>
      <ScrollView contentContainerStyle={{ padding: 20, paddingBottom: 40 }}>
        {/* Main result card */}
        <View style={{ backgroundColor: COLORS.white, borderRadius: RADIUS.xl, padding: 28, alignItems: 'center', marginBottom: 16, ...SHADOWS.medium }}>
          <View style={{ width: 90, height: 90, borderRadius: 45, backgroundColor: c.iconBg, alignItems: 'center', justifyContent: 'center', marginBottom: 20 }}>
            <Ionicons name={c.icon} size={56} color={c.iconColor} />
          </View>
          <Text style={{ fontSize: 22, fontWeight: '800', color: COLORS.textPrimary, textAlign: 'center', marginBottom: 8 }}>{c.title}</Text>
          <Text style={{ color: COLORS.textSecondary, fontSize: 14, textAlign: 'center', lineHeight: 22, marginBottom: 16 }}>{c.subtitle}</Text>

          {/* Order details */}
          <View style={{ backgroundColor: COLORS.background, borderRadius: RADIUS.md, padding: 14, width: '100%', alignItems: 'center' }}>
            <Text style={{ color: COLORS.textSecondary, fontSize: 13 }}>Order {orderNum}</Text>
            {payment.amount > 0 && (
              <Text style={{ fontWeight: '800', fontSize: 18, color: COLORS.textPrimary, marginTop: 4 }}>₹{parseFloat(payment.amount).toFixed(0)}</Text>
            )}
          </View>
        </View>

        {/* AUREV AI analysis card */}
        {c.showAurev && payment.ml_classification && (
          <View style={{ backgroundColor: COLORS.white, borderRadius: RADIUS.md, padding: 16, marginBottom: 16, ...SHADOWS.small }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 }}>
              <Ionicons name="hardware-chip" size={18} color={COLORS.primary} />
              <Text style={{ fontWeight: '700', color: COLORS.textPrimary, fontSize: 14 }}>AUREV AI Analysis</Text>
            </View>
            {[
              { label: 'Failure Type', value: payment.ml_classification },
              { label: 'Confidence', value: payment.ml_confidence ? `${(payment.ml_confidence * 100).toFixed(0)}%` : null },
              { label: 'Action Taken', value: payment.aurev_action },
            ].filter(x => x.value).map(({ label, value }) => (
              <View key={label} style={{ flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6, borderBottomWidth: 1, borderBottomColor: COLORS.border }}>
                <Text style={{ color: COLORS.textSecondary, fontSize: 13 }}>{label}</Text>
                <Text style={{ fontWeight: '700', color: COLORS.primary, fontSize: 13 }}>{value}</Text>
              </View>
            ))}
          </View>
        )}

        {/* CTA buttons */}
        <View style={{ gap: 12 }}>
          {isSuccess ? (
            <>
              <TouchableOpacity
                onPress={() => router.push('/(tabs)/orders')}
                style={{ backgroundColor: COLORS.primary, borderRadius: RADIUS.md, paddingVertical: 16, alignItems: 'center' }}
              >
                <Text style={{ color: 'white', fontWeight: '700', fontSize: 16 }}>Track Order</Text>
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => router.replace('/(tabs)/categories')}
                style={{ backgroundColor: COLORS.white, borderRadius: RADIUS.md, paddingVertical: 16, alignItems: 'center', borderWidth: 1.5, borderColor: COLORS.border }}
              >
                <Text style={{ fontWeight: '700', fontSize: 16, color: COLORS.textPrimary }}>Continue Shopping</Text>
              </TouchableOpacity>
            </>
          ) : (
            <>
              <TouchableOpacity
                onPress={() => router.replace('/checkout')}
                style={{ backgroundColor: COLORS.error, borderRadius: RADIUS.md, paddingVertical: 16, alignItems: 'center' }}
              >
                <Text style={{ color: 'white', fontWeight: '700', fontSize: 16 }}>Try Again</Text>
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => router.replace('/(tabs)/orders')}
                style={{ backgroundColor: COLORS.white, borderRadius: RADIUS.md, paddingVertical: 16, alignItems: 'center', borderWidth: 1.5, borderColor: COLORS.border }}
              >
                <Text style={{ fontWeight: '700', fontSize: 16, color: COLORS.textPrimary }}>Check Order Status</Text>
              </TouchableOpacity>
            </>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}
