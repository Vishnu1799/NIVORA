import { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, SafeAreaView, KeyboardAvoidingView, Platform, ScrollView, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuthStore } from '../../store/authStore';
import { COLORS, SHADOWS, RADIUS } from '../../constants/theme';
import NivoraLogo from '../../components/NivoraLogo';

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login } = useAuthStore();
  const router = useRouter();

  const handleLogin = async () => {
    if (!email || !password) { Alert.alert('Error', 'Please fill all fields'); return; }
    setLoading(true);
    try {
      const data = await login(email.trim(), password);
      router.replace(data.role === 'MERCHANT' ? '/(tabs)/account' : '/(tabs)');
    } catch (err) {
      Alert.alert('Login Failed', err.response?.data?.detail || 'Invalid credentials');
    } finally { setLoading(false); }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: COLORS.white }}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={{ flexGrow: 1, padding: 24 }} keyboardShouldPersistTaps="handled">
          <TouchableOpacity onPress={() => router.back()} style={{ marginBottom: 32, alignSelf: 'flex-start' }}>
            <Ionicons name="arrow-back" size={24} color={COLORS.textPrimary} />
          </TouchableOpacity>

          <NivoraLogo size="md" />
          <Text style={{ fontSize: 26, fontWeight: '800', color: COLORS.textPrimary, marginTop: 24, marginBottom: 4 }}>Welcome back!</Text>
          <Text style={{ color: COLORS.textSecondary, fontSize: 15, marginBottom: 32 }}>Sign in to your account</Text>

          <View style={{ gap: 16 }}>
            <View>
              <Text style={{ fontWeight: '600', color: COLORS.textPrimary, marginBottom: 8, fontSize: 14 }}>Email Address</Text>
              <TextInput
                value={email} onChangeText={setEmail}
                placeholder="you@example.com" keyboardType="email-address" autoCapitalize="none"
                style={{ backgroundColor: COLORS.background, borderRadius: RADIUS.md, padding: 14, fontSize: 15, borderWidth: 1, borderColor: COLORS.border, color: COLORS.textPrimary }}
              />
            </View>
            <View>
              <Text style={{ fontWeight: '600', color: COLORS.textPrimary, marginBottom: 8, fontSize: 14 }}>Password</Text>
              <View style={{ position: 'relative' }}>
                <TextInput
                  value={password} onChangeText={setPassword}
                  placeholder="Enter password" secureTextEntry={!showPass}
                  style={{ backgroundColor: COLORS.background, borderRadius: RADIUS.md, padding: 14, fontSize: 15, borderWidth: 1, borderColor: COLORS.border, color: COLORS.textPrimary, paddingRight: 50 }}
                />
                <TouchableOpacity onPress={() => setShowPass(!showPass)} style={{ position: 'absolute', right: 14, top: 16 }}>
                  <Ionicons name={showPass ? 'eye-off-outline' : 'eye-outline'} size={20} color={COLORS.textLight} />
                </TouchableOpacity>
              </View>
            </View>

            <TouchableOpacity onPress={handleLogin} disabled={loading}
              style={{ backgroundColor: loading ? '#9CC4B2' : COLORS.primary, borderRadius: RADIUS.md, paddingVertical: 16, alignItems: 'center', marginTop: 8 }}
            >
              <Text style={{ color: 'white', fontWeight: '700', fontSize: 16 }}>{loading ? 'Signing in...' : 'Sign In'}</Text>
            </TouchableOpacity>
          </View>

          {/* Demo accounts */}
          <View style={{ backgroundColor: COLORS.background, borderRadius: RADIUS.md, padding: 14, marginTop: 24 }}>
            <Text style={{ fontWeight: '700', color: COLORS.textSecondary, fontSize: 12, marginBottom: 8 }}>DEMO ACCOUNTS</Text>
            <TouchableOpacity onPress={() => { setEmail('customer@nivora.com'); setPassword('demo123'); }}>
              <Text style={{ color: COLORS.primary, fontSize: 13, paddingVertical: 4, fontWeight: '500' }}>👤 Customer: customer@nivora.com / demo123</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={() => { setEmail('merchant@nivora.com'); setPassword('demo123'); }}>
              <Text style={{ color: COLORS.primary, fontSize: 13, paddingVertical: 4, fontWeight: '500' }}>🏪 Merchant: merchant@nivora.com / demo123</Text>
            </TouchableOpacity>
          </View>

          <TouchableOpacity onPress={() => router.push('/auth/register')} style={{ alignItems: 'center', marginTop: 20 }}>
            <Text style={{ color: COLORS.textSecondary, fontSize: 14 }}>Don't have an account? <Text style={{ color: COLORS.primary, fontWeight: '700' }}>Register</Text></Text>
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
