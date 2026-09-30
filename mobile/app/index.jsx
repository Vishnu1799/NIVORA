import { View, Text, Image, TouchableOpacity, SafeAreaView, Dimensions } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../constants/theme';
import NivoraLogo from '../components/NivoraLogo';

export default function SplashScreen() {
  const router = useRouter();
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: COLORS.white }}>
      {/* Top section */}
      <View style={{ paddingHorizontal: 28, paddingTop: 40, alignItems: 'center' }}>
        <NivoraLogo size="lg" />
        <Text style={{ fontSize: 26, fontWeight: '700', color: COLORS.textPrimary, textAlign: 'center', marginTop: 20, lineHeight: 34 }}>
          Fresh Groceries{"\n"}Delivered to Your Door
        </Text>
      </View>

      {/* Features row */}
      <View style={{ flexDirection: 'row', justifyContent: 'center', gap: 24, marginTop: 24, paddingHorizontal: 28 }}>
        {[
          { icon: 'shield-checkmark-outline', label: 'Fresh &\nQuality' },
          { icon: 'grid-outline', label: 'Wide\nVariety' },
          { icon: 'bicycle-outline', label: 'Fast\nDelivery' },
        ].map((f) => (
          <View key={f.label} style={{ alignItems: 'center', gap: 6 }}>
            <View style={{ width: 52, height: 52, borderRadius: 16, backgroundColor: COLORS.primaryLight, alignItems: 'center', justifyContent: 'center' }}>
              <Ionicons name={f.icon} size={26} color={COLORS.primary} />
            </View>
            <Text style={{ fontSize: 11, color: COLORS.textSecondary, textAlign: 'center', fontWeight: '500' }}>{f.label}</Text>
          </View>
        ))}
      </View>

      {/* Hero image */}
      <View style={{ flex: 1, marginTop: 24, overflow: 'hidden' }}>
        <Image
          source={{ uri: 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=600&q=80' }}
          style={{ width: '100%', height: '100%' }}
          resizeMode="cover"
        />
      </View>

      {/* CTA */}
      <View style={{ padding: 24, backgroundColor: COLORS.white }}>
        <TouchableOpacity
          onPress={() => router.replace('/(tabs)')}
          style={{
            backgroundColor: COLORS.primary,
            borderRadius: 14,
            paddingVertical: 16,
            alignItems: 'center',
            flexDirection: 'row',
            justifyContent: 'center',
            gap: 8,
          }}
        >
          <Text style={{ color: 'white', fontWeight: '700', fontSize: 17 }}>Get Started</Text>
          <Ionicons name="arrow-forward" size={18} color="white" />
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}
