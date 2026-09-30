import { useState } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, Image,
  SafeAreaView
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { COLORS, SHADOWS, RADIUS, PRODUCTS, CATEGORIES } from '../../constants/theme';
import NivoraLogo from '../../components/NivoraLogo';
import { useAuthStore } from '../../store/authStore';

const POPULAR = PRODUCTS.slice(0, 4);
const CATEGORY_ICONS = CATEGORIES.slice(0, 4);

export default function HomeScreen() {
  const router = useRouter();
  const { user } = useAuthStore();

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: COLORS.white }}>
      <ScrollView showsVerticalScrollIndicator={false} stickyHeaderIndices={[0]}>
        {/* Sticky Header */}
        <View style={{ backgroundColor: COLORS.white, paddingHorizontal: 16, paddingTop: 12, paddingBottom: 8 }}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <NivoraLogo size="md" />
            <View style={{ flexDirection: 'row', gap: 12 }}>
              <TouchableOpacity style={{ padding: 4 }}>
                <Ionicons name="notifications-outline" size={24} color={COLORS.textPrimary} />
              </TouchableOpacity>
              <TouchableOpacity onPress={() => router.push('/(tabs)/account')}>
                <View style={{ width: 36, height: 36, borderRadius: 18, backgroundColor: COLORS.primaryLight, alignItems: 'center', justifyContent: 'center' }}>
                  <Ionicons name="person" size={20} color={COLORS.primary} />
                </View>
              </TouchableOpacity>
            </View>
          </View>
          {/* Search bar */}
          <TouchableOpacity
            onPress={() => router.push('/(tabs)/categories')}
            style={{
              flexDirection: 'row', alignItems: 'center', gap: 10,
              backgroundColor: '#F5F7FA', borderRadius: 12, paddingHorizontal: 14, paddingVertical: 12,
              borderWidth: 1, borderColor: '#E5E7EB',
            }}
          >
            <Ionicons name="search" size={18} color="#9CA3AF" />
            <Text style={{ color: '#9CA3AF', fontSize: 14, flex: 1 }}>Search for fruits, vegetables, milk...</Text>
          </TouchableOpacity>
        </View>

        {/* Hero banner */}
        <View style={{ marginHorizontal: 16, marginTop: 12, borderRadius: RADIUS.lg, overflow: 'hidden', ...SHADOWS.medium }}>
          <Image
            source={{ uri: 'https://images.unsplash.com/photo-1610832958506-aa56368176cf?w=600&q=80' }}
            style={{ width: '100%', height: 160 }}
            resizeMode="cover"
          />
          <View style={{
            position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: 'rgba(22,114,68,0.72)',
            padding: 20, justifyContent: 'center',
          }}>
            <Text style={{ color: 'white', fontSize: 20, fontWeight: '800', lineHeight: 26 }}>Fresh Fruits{"\n"}& Vegetables</Text>
            <Text style={{ color: 'rgba(255,255,255,0.85)', fontSize: 13, marginTop: 4 }}>Healthy choices for a better you.</Text>
            <TouchableOpacity
              onPress={() => router.push('/(tabs)/categories')}
              style={{ marginTop: 14, backgroundColor: 'white', paddingHorizontal: 18, paddingVertical: 8, borderRadius: 20, alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center', gap: 6 }}
            >
              <Text style={{ color: COLORS.primary, fontWeight: '700', fontSize: 13 }}>Shop Now</Text>
              <Ionicons name="arrow-forward" size={14} color={COLORS.primary} />
            </TouchableOpacity>
          </View>
        </View>

        {/* Category icons row */}
        <View style={{ paddingHorizontal: 16, marginTop: 20 }}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
            {CATEGORY_ICONS.map((cat) => (
              <TouchableOpacity
                key={cat.id}
                onPress={() => router.push({ pathname: '/category/[id]', params: { id: cat.id, name: cat.name } })}
                style={{ alignItems: 'center', gap: 6, flex: 1 }}
              >
                <View style={{ width: 64, height: 64, borderRadius: 16, overflow: 'hidden', ...SHADOWS.small }}>
                  <Image source={{ uri: cat.image }} style={{ width: '100%', height: '100%' }} resizeMode="cover" />
                </View>
                <Text style={{ fontSize: 11, color: COLORS.textSecondary, textAlign: 'center', fontWeight: '500' }} numberOfLines={2}>
                  {cat.name.split(' ')[0]}{"\n"}{cat.name.split(' ').slice(1).join(' ')}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Popular Near You */}
        <View style={{ marginTop: 24, paddingHorizontal: 16 }}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <Text style={{ fontSize: 17, fontWeight: '700', color: COLORS.textPrimary }}>Popular Near You</Text>
            <TouchableOpacity onPress={() => router.push('/(tabs)/categories')}>
              <Text style={{ color: COLORS.primary, fontWeight: '600', fontSize: 13 }}>View All →</Text>
            </TouchableOpacity>
          </View>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginHorizontal: -4 }}>
            {POPULAR.map((p) => (
              <TouchableOpacity key={p.id} onPress={() => router.push({ pathname: '/product/[id]', params: { id: p.id } })} style={{ width: 130, marginHorizontal: 4 }}>
                <View style={{ backgroundColor: COLORS.white, borderRadius: RADIUS.md, ...SHADOWS.small, overflow: 'hidden' }}>
                  <Image source={{ uri: p.image }} style={{ width: '100%', height: 90 }} resizeMode="cover" />
                  <View style={{ padding: 10 }}>
                    <Text style={{ fontWeight: '700', color: COLORS.textPrimary, fontSize: 13 }} numberOfLines={1}>{p.name}</Text>
                    <Text style={{ color: COLORS.textLight, fontSize: 11, marginTop: 1 }}>{p.unit}</Text>
                    <Text style={{ color: COLORS.primary, fontWeight: '800', fontSize: 14, marginTop: 4 }}>₹{p.price}</Text>
                  </View>
                </View>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        <View style={{ height: 20 }} />
      </ScrollView>
    </SafeAreaView>
  );
}
