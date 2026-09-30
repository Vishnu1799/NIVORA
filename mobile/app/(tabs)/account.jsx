import { View, Text, TouchableOpacity, SafeAreaView, ScrollView, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useAuthStore } from '../../store/authStore';
import { COLORS, SHADOWS, RADIUS } from '../../constants/theme';
import NivoraLogo from '../../components/NivoraLogo';

const MENU_ITEMS = [
  { icon: 'location-outline', label: 'My Addresses', route: null },
  { icon: 'receipt-outline', label: 'Order History', route: '/(tabs)/orders' },
  { icon: 'analytics-outline', label: 'AUREV AI Dashboard', route: '/aurev-dashboard', highlight: true },
  { icon: 'notifications-outline', label: 'Notifications', route: null },
  { icon: 'help-circle-outline', label: 'Help & Support', route: null },
  { icon: 'information-circle-outline', label: 'About NIVORA', route: null },
];

export default function AccountScreen() {
  const { user, isAuthenticated, logout } = useAuthStore();
  const router = useRouter();

  const handleLogout = () => {
    Alert.alert('Sign Out', 'Are you sure you want to sign out?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Sign Out', style: 'destructive', onPress: async () => { await logout(); router.replace('/'); } },
    ]);
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: COLORS.background }}>
      <ScrollView>
        {/* Profile section */}
        <View style={{ backgroundColor: COLORS.white, padding: 20, alignItems: 'center' }}>
          <View style={{ width: 72, height: 72, borderRadius: 36, backgroundColor: COLORS.primaryLight, alignItems: 'center', justifyContent: 'center', marginBottom: 12 }}>
            <Ionicons name="person" size={36} color={COLORS.primary} />
          </View>
          {isAuthenticated ? (
            <>
              <Text style={{ fontSize: 18, fontWeight: '700', color: COLORS.textPrimary }}>{user?.name}</Text>
              <Text style={{ color: COLORS.textSecondary, fontSize: 14, marginTop: 4 }}>{user?.role}</Text>
            </>
          ) : (
            <>
              <TouchableOpacity onPress={() => router.push('/auth/login')} style={{ backgroundColor: COLORS.primary, paddingHorizontal: 32, paddingVertical: 12, borderRadius: RADIUS.md, marginTop: 4 }}>
                <Text style={{ color: 'white', fontWeight: '700', fontSize: 15 }}>Sign In</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={() => router.push('/auth/register')} style={{ marginTop: 12 }}>
                <Text style={{ color: COLORS.primary, fontWeight: '600' }}>Create Account</Text>
              </TouchableOpacity>
            </>
          )}
        </View>

        {/* Menu */}
        <View style={{ margin: 16, backgroundColor: COLORS.white, borderRadius: RADIUS.md, ...SHADOWS.small }}>
          {MENU_ITEMS.map((item, i) => (
            <TouchableOpacity
              key={item.label}
              onPress={() => item.route && router.push(item.route)}
              style={{
                flexDirection: 'row', alignItems: 'center', padding: 16, gap: 14,
                borderBottomWidth: i < MENU_ITEMS.length - 1 ? 1 : 0, borderBottomColor: COLORS.border,
              }}
            >
              <Ionicons name={item.icon} size={22} color={item.highlight ? COLORS.primary : COLORS.textSecondary} />
              <Text style={{ flex: 1, fontSize: 15, color: item.highlight ? COLORS.primary : COLORS.textPrimary, fontWeight: item.highlight ? '700' : '500' }}>{item.label}</Text>
              <Ionicons name="chevron-forward" size={18} color={COLORS.textLight} />
            </TouchableOpacity>
          ))}
        </View>

        {isAuthenticated && (
          <TouchableOpacity onPress={handleLogout} style={{ margin: 16, marginTop: 0, backgroundColor: '#FFF0EF', borderRadius: RADIUS.md, padding: 16, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
            <Ionicons name="log-out-outline" size={20} color={COLORS.error} />
            <Text style={{ color: COLORS.error, fontWeight: '700', fontSize: 15 }}>Sign Out</Text>
          </TouchableOpacity>
        )}

        <View style={{ alignItems: 'center', paddingBottom: 20 }}>
          <NivoraLogo size="sm" />
          <Text style={{ color: COLORS.textLight, fontSize: 11, marginTop: 4 }}>v1.0.0 • Powered by AUREV AI</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}
