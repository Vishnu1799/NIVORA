import { View, Text, Image, ScrollView, TouchableOpacity, SafeAreaView } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, SHADOWS, RADIUS, PRODUCTS } from '../../constants/theme';
import { useCartStore } from '../../store/cartStore';

export default function ProductDetail() {
  const { id } = useLocalSearchParams();
  const router = useRouter();
  const product = PRODUCTS.find((p) => p.id === id) || PRODUCTS[0];
  const { items, addItem, updateQty } = useCartStore();
  const cartItem = items.find((i) => i.id === product.id);

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: COLORS.white }}>
      {/* Back button over image */}
      <View style={{ position: 'relative' }}>
        <Image source={{ uri: product.image }} style={{ width: '100%', height: 280 }} resizeMode="cover" />
        <TouchableOpacity
          onPress={() => router.back()}
          style={{ position: 'absolute', top: 16, left: 16, width: 38, height: 38, borderRadius: 19, backgroundColor: 'rgba(255,255,255,0.9)', alignItems: 'center', justifyContent: 'center', ...SHADOWS.small }}
        >
          <Ionicons name="arrow-back" size={20} color={COLORS.textPrimary} />
        </TouchableOpacity>
        <TouchableOpacity
          style={{ position: 'absolute', top: 16, right: 16, width: 38, height: 38, borderRadius: 19, backgroundColor: 'rgba(255,255,255,0.9)', alignItems: 'center', justifyContent: 'center', ...SHADOWS.small }}
        >
          <Ionicons name="heart-outline" size={20} color={COLORS.textPrimary} />
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={{ padding: 20 }}>
        <Text style={{ fontSize: 22, fontWeight: '800', color: COLORS.textPrimary }}>{product.name}</Text>
        <Text style={{ color: COLORS.textSecondary, fontSize: 13, marginTop: 4 }}>{product.unit} • {product.subtitle?.split('•')[1]?.trim()}</Text>

        <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 12 }}>
          <Text style={{ fontSize: 28, fontWeight: '800', color: COLORS.textPrimary }}>₹{product.price}</Text>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
            <Ionicons name="star" size={16} color="#F59E0B" />
            <Text style={{ fontWeight: '700', color: COLORS.textPrimary }}>{product.rating}</Text>
            <Text style={{ color: COLORS.textLight, fontSize: 13 }}>({(product.reviews / 1000).toFixed(1)}k reviews)</Text>
          </View>
        </View>

        <View style={{ height: 1, backgroundColor: COLORS.border, marginVertical: 16 }} />

        <Text style={{ fontWeight: '700', fontSize: 15, color: COLORS.textPrimary, marginBottom: 8 }}>Product Description</Text>
        <Text style={{ color: COLORS.textSecondary, lineHeight: 22, fontSize: 14 }}>{product.description}</Text>

        <View style={{ height: 1, backgroundColor: COLORS.border, marginVertical: 16 }} />

        <Text style={{ fontWeight: '700', fontSize: 15, color: COLORS.textPrimary, marginBottom: 12 }}>Quantity</Text>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 20 }}>
          <TouchableOpacity
            onPress={() => cartItem && updateQty(product.id, cartItem.qty - 1)}
            style={{ width: 36, height: 36, borderRadius: 18, borderWidth: 1.5, borderColor: COLORS.border, alignItems: 'center', justifyContent: 'center' }}
          >
            <Ionicons name="remove" size={18} color={COLORS.textPrimary} />
          </TouchableOpacity>
          <Text style={{ fontWeight: '700', fontSize: 18, minWidth: 30, textAlign: 'center' }}>{cartItem?.qty || 0}</Text>
          <TouchableOpacity
            onPress={() => addItem(product)}
            style={{ width: 36, height: 36, borderRadius: 18, borderWidth: 1.5, borderColor: COLORS.border, alignItems: 'center', justifyContent: 'center' }}
          >
            <Ionicons name="add" size={18} color={COLORS.textPrimary} />
          </TouchableOpacity>
        </View>
      </ScrollView>

      {/* Add to Cart button */}
      <View style={{ padding: 16, backgroundColor: COLORS.white, borderTopWidth: 1, borderTopColor: COLORS.border }}>
        <TouchableOpacity
          onPress={() => { addItem(product); router.push('/(tabs)/cart'); }}
          style={{ backgroundColor: COLORS.primary, borderRadius: RADIUS.md, paddingVertical: 16, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10 }}
        >
          <Ionicons name="cart-outline" size={20} color="white" />
          <Text style={{ color: 'white', fontWeight: '700', fontSize: 16 }}>Add to Cart</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}
