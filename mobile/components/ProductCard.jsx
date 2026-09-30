import { View, Text, Image, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, SHADOWS, RADIUS } from '../constants/theme';
import { useCartStore } from '../store/cartStore';

export default function ProductCard({ product, layout = 'grid' }) {
  const { items, addItem, updateQty } = useCartStore();
  const cartItem = items.find((i) => i.id === product.id);

  if (layout === 'list') {
    return (
      <View style={{
        backgroundColor: COLORS.white,
        borderRadius: RADIUS.md,
        padding: 12,
        flexDirection: 'row',
        alignItems: 'center',
        gap: 12,
        marginBottom: 10,
        ...SHADOWS.small,
      }}>
        <Image source={{ uri: product.image }} style={{ width: 64, height: 64, borderRadius: 10 }} resizeMode="cover" />
        <View style={{ flex: 1 }}>
          <Text style={{ fontWeight: '700', color: COLORS.textPrimary, fontSize: 14 }}>{product.name}</Text>
          <Text style={{ color: COLORS.textLight, fontSize: 12, marginTop: 2 }}>{product.unit}</Text>
          <Text style={{ color: COLORS.primary, fontWeight: '800', fontSize: 15, marginTop: 4 }}>₹{product.price}</Text>
        </View>
        {cartItem ? (
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: COLORS.primaryLight, borderRadius: 20, paddingHorizontal: 8, paddingVertical: 4 }}>
            <TouchableOpacity onPress={() => updateQty(product.id, cartItem.qty - 1)}>
              <Ionicons name="remove" size={18} color={COLORS.primary} />
            </TouchableOpacity>
            <Text style={{ fontWeight: '700', color: COLORS.primary, minWidth: 16, textAlign: 'center' }}>{cartItem.qty}</Text>
            <TouchableOpacity onPress={() => addItem(product)}>
              <Ionicons name="add" size={18} color={COLORS.primary} />
            </TouchableOpacity>
          </View>
        ) : (
          <TouchableOpacity
            onPress={() => addItem(product)}
            style={{ backgroundColor: COLORS.primary, borderRadius: 20, paddingHorizontal: 16, paddingVertical: 6, flexDirection: 'row', alignItems: 'center', gap: 4 }}
          >
            <Ionicons name="add" size={14} color="white" />
            <Text style={{ color: 'white', fontWeight: '700', fontSize: 13 }}>Add</Text>
          </TouchableOpacity>
        )}
      </View>
    );
  }

  return (
    <View style={{
      backgroundColor: COLORS.white,
      borderRadius: RADIUS.md,
      padding: 12,
      flex: 1,
      margin: 5,
      ...SHADOWS.small,
    }}>
      <Image source={{ uri: product.image }} style={{ width: '100%', height: 90, borderRadius: 8, marginBottom: 8 }} resizeMode="cover" />
      <Text style={{ fontWeight: '700', color: COLORS.textPrimary, fontSize: 13 }} numberOfLines={1}>{product.name}</Text>
      <Text style={{ color: COLORS.textLight, fontSize: 11, marginTop: 2 }}>{product.unit}</Text>
      <Text style={{ color: COLORS.primary, fontWeight: '800', fontSize: 15, marginTop: 4 }}>₹{product.price}</Text>
      {cartItem ? (
        <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 8, backgroundColor: COLORS.primaryLight, borderRadius: 20, paddingHorizontal: 10, paddingVertical: 4 }}>
          <TouchableOpacity onPress={() => updateQty(product.id, cartItem.qty - 1)}>
            <Ionicons name="remove" size={18} color={COLORS.primary} />
          </TouchableOpacity>
          <Text style={{ fontWeight: '700', color: COLORS.primary }}>{cartItem.qty}</Text>
          <TouchableOpacity onPress={() => addItem(product)}>
            <Ionicons name="add" size={18} color={COLORS.primary} />
          </TouchableOpacity>
        </View>
      ) : (
        <TouchableOpacity
          onPress={() => addItem(product)}
          style={{ marginTop: 8, backgroundColor: COLORS.primary, borderRadius: 20, paddingVertical: 6, alignItems: 'center', flexDirection: 'row', justifyContent: 'center', gap: 4 }}
        >
          <Ionicons name="add" size={14} color="white" />
          <Text style={{ color: 'white', fontWeight: '700', fontSize: 13 }}>Add</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}
