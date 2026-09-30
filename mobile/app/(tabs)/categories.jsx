import { View, Text, FlatList, TouchableOpacity, Image, SafeAreaView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { COLORS, SHADOWS, RADIUS, CATEGORIES } from '../../constants/theme';

export default function CategoriesScreen() {
  const router = useRouter();
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: COLORS.background }}>
      <View style={{ backgroundColor: COLORS.white, paddingHorizontal: 16, paddingTop: 16, paddingBottom: 12, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', ...SHADOWS.small }}>
        <Text style={{ fontSize: 20, fontWeight: '800', color: COLORS.textPrimary }}>Categories</Text>
        <TouchableOpacity><Ionicons name="search-outline" size={22} color={COLORS.textPrimary} /></TouchableOpacity>
      </View>
      <FlatList
        data={CATEGORIES}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ padding: 16, gap: 12 }}
        renderItem={({ item }) => (
          <TouchableOpacity
            onPress={() => router.push({ pathname: '/category/[id]', params: { id: item.id, name: item.name } })}
            style={{
              backgroundColor: COLORS.white,
              borderRadius: RADIUS.md,
              padding: 14,
              flexDirection: 'row',
              alignItems: 'center',
              gap: 14,
              ...SHADOWS.small,
            }}
          >
            <Image source={{ uri: item.image }} style={{ width: 60, height: 60, borderRadius: 10 }} resizeMode="cover" />
            <View style={{ flex: 1 }}>
              <Text style={{ fontSize: 15, fontWeight: '700', color: COLORS.textPrimary }}>{item.name}</Text>
              <Text style={{ fontSize: 12, color: COLORS.textSecondary, marginTop: 3 }}>{item.desc}</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color={COLORS.textLight} />
          </TouchableOpacity>
        )}
      />
    </SafeAreaView>
  );
}
