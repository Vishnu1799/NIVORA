import { View, Text, FlatList, TouchableOpacity, Image, SafeAreaView } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useCartStore } from '../../store/cartStore';
import { useAuthStore } from '../../store/authStore';
import { COLORS, SHADOWS, RADIUS } from '../../constants/theme';

export default function CartScreen() {
  const { items, updateQty, removeItem, getTotal } = useCartStore();
  const { isAuthenticated } = useAuthStore();
  const router = useRouter();
  const total = getTotal();
  const DELIVERY = 20;

  if (items.length === 0) return (
    <SafeAreaView style={{ flex: 1, backgroundColor: COLORS.background, alignItems: 'center', justifyContent: 'center', padding: 32 }}>
      <Ionicons name="cart-outline" size={80} color="#E5E7EB" />
      <Text style={{ fontSize: 20, fontWeight: '700', color: COLORS.textSecondary, marginTop: 20, marginBottom: 8 }}>Your cart is empty</Text>
      <Text style={{ color: COLORS.textLight, textAlign: 'center', marginBottom: 28 }}>Add fresh groceries to get started</Text>
      <TouchableOpacity onPress={() => router.push('/(tabs)/categories')} style={{ backgroundColor: COLORS.primary, paddingHorizontal: 32, paddingVertical: 14, borderRadius: RADIUS.md }}>
        <Text style={{ color: 'white', fontWeight: '700', fontSize: 16 }}>Shop Now</Text>
      </TouchableOpacity>
    </SafeAreaView>
  );

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: COLORS.background }}>
      {/* Header */}
      <View style={{ backgroundColor: COLORS.white, paddingHorizontal: 16, paddingTop: 16, paddingBottom: 12 }}>
        <Text style={{ fontSize: 20, fontWeight: '800', color: COLORS.textPrimary }}>My Cart</Text>
        <Text style={{ color: COLORS.textSecondary, fontSize: 13, marginTop: 2 }}>{items.length} item{items.length !== 1 ? 's' : ''}</Text>
      </View>

      <FlatList
        data={items}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ padding: 16, paddingBottom: 8 }}
        renderItem={({ item }) => (
          <View style={{ backgroundColor: COLORS.white, borderRadius: RADIUS.md, padding: 12, marginBottom: 10, flexDirection: 'row', alignItems: 'center', gap: 12, ...SHADOWS.small }}>
            <Image source={{ uri: item.image }} style={{ width: 64, height: 64, borderRadius: 10 }} resizeMode="cover" />
            <View style={{ flex: 1 }}>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Text style={{ fontWeight: '700', color: COLORS.textPrimary, fontSize: 14, flex: 1 }}>{item.name}</Text>
                <TouchableOpacity onPress={() => removeItem(item.id)} style={{ padding: 4 }}>
                  <Ionicons name="trash-outline" size={16} color="#9CA3AF" />
                </TouchableOpacity>
              </View>
              <Text style={{ color: COLORS.textLight, fontSize: 12, marginTop: 2 }}>{item.unit}</Text>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
                <Text style={{ color: COLORS.primary, fontWeight: '800', fontSize: 15 }}>₹{item.price}</Text>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 14 }}>
                  <TouchableOpacity onPress={() => updateQty(item.id, item.qty - 1)} style={{ width: 28, height: 28, borderRadius: 14, borderWidth: 1.5, borderColor: COLORS.border, alignItems: 'center', justifyContent: 'center' }}>
                    <Ionicons name="remove" size={14} color={COLORS.textPrimary} />
                  </TouchableOpacity>
                  <Text style={{ fontWeight: '700', fontSize: 15, minWidth: 20, textAlign: 'center' }}>{item.qty}</Text>
                  <TouchableOpacity onPress={() => updateQty(item.id, item.qty + 1)} style={{ width: 28, height: 28, borderRadius: 14, backgroundColor: COLORS.primary, alignItems: 'center', justifyContent: 'center' }}>
                    <Ionicons name="add" size={14} color="white" />
                  </TouchableOpacity>
                </View>
              </View>
            </View>
          </View>
        )}
        ListFooterComponent={
          <View style={{ backgroundColor: COLORS.white, borderRadius: RADIUS.md, padding: 16, marginTop: 4, ...SHADOWS.small }}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6 }}>
              <Text style={{ color: COLORS.textSecondary, fontSize: 14 }}>Subtotal</Text>
              <Text style={{ fontWeight: '600', fontSize: 14, color: COLORS.textPrimary }}>₹{total.toFixed(0)}</Text>
            </View>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6 }}>
              <Text style={{ color: COLORS.textSecondary, fontSize: 14 }}>Delivery Fee</Text>
              <Text style={{ fontWeight: '600', fontSize: 14, color: COLORS.textPrimary }}>₹{DELIVERY}</Text>
            </View>
            <View style={{ height: 1, backgroundColor: COLORS.border, marginVertical: 8 }} />
            <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
              <Text style={{ fontWeight: '700', fontSize: 16, color: COLORS.textPrimary }}>Total</Text>
              <Text style={{ fontWeight: '800', fontSize: 18, color: COLORS.textPrimary }}>₹{(total + DELIVERY).toFixed(0)}</Text>
            </View>
          </View>
        }
      />

      {/* Bottom CTA */}
      <View style={{ padding: 16, backgroundColor: COLORS.white, borderTopWidth: 1, borderTopColor: COLORS.border }}>
        <TouchableOpacity
          onPress={() => { if (!isAuthenticated) { router.push('/auth/login'); return; } router.push('/checkout'); }}
          style={{ backgroundColor: COLORS.primary, borderRadius: RADIUS.md, paddingVertical: 16, alignItems: 'center' }}
        >
          <Text style={{ color: 'white', fontWeight: '700', fontSize: 16 }}>Proceed to Checkout</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}
