import { useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, SafeAreaView, ScrollView } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, RADIUS, PRODUCTS, CATEGORIES } from '../../constants/theme';
import ProductCard from '../../components/ProductCard';

const FILTER_TABS = ['All', 'Fruits', 'Vegetables', 'Herbs'];

export default function CategoryScreen() {
  const { id, name } = useLocalSearchParams();
  const router = useRouter();
  const [filter, setFilter] = useState('All');
  const category = CATEGORIES.find((c) => c.id === id);
  const products = PRODUCTS.filter((p) => !id || p.category === (category?.name || name));
  const displayProducts = products.length > 0 ? products : PRODUCTS.slice(0, 6);

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: COLORS.background }}>
      {/* Header */}
      <View style={{ backgroundColor: COLORS.white, paddingHorizontal: 16, paddingTop: 12, paddingBottom: 10 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <TouchableOpacity onPress={() => router.back()} style={{ padding: 4 }}>
            <Ionicons name="arrow-back" size={24} color={COLORS.textPrimary} />
          </TouchableOpacity>
          <Text style={{ fontSize: 17, fontWeight: '700', color: COLORS.textPrimary, flex: 1, marginLeft: 12 }}>{name || category?.name || 'Products'}</Text>
          <TouchableOpacity><Ionicons name="search-outline" size={22} color={COLORS.textPrimary} /></TouchableOpacity>
        </View>
        {/* Filter tabs */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View style={{ flexDirection: 'row', gap: 8 }}>
            {FILTER_TABS.map((t) => (
              <TouchableOpacity
                key={t}
                onPress={() => setFilter(t)}
                style={{
                  paddingHorizontal: 16, paddingVertical: 7, borderRadius: 20,
                  backgroundColor: filter === t ? COLORS.primary : COLORS.white,
                  borderWidth: 1, borderColor: filter === t ? COLORS.primary : COLORS.border,
                }}
              >
                <Text style={{ fontWeight: '600', fontSize: 13, color: filter === t ? 'white' : COLORS.textSecondary }}>{t}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>
      </View>

      {/* Product list */}
      <FlatList
        data={displayProducts}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ padding: 16 }}
        renderItem={({ item }) => (
          <TouchableOpacity onPress={() => router.push({ pathname: '/product/[id]', params: { id: item.id } })}>
            <ProductCard product={item} layout="list" />
          </TouchableOpacity>
        )}
      />
    </SafeAreaView>
  );
}
