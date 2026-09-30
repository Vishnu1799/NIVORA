import { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, SafeAreaView, KeyboardAvoidingView, Platform, ScrollView, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuthStore } from '../../store/authStore';
import { COLORS, RADIUS } from '../../constants/theme';
import NivoraLogo from '../../components/NivoraLogo';

export default function RegisterScreen() {
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'CUSTOMER' });
  const [loading, setLoading] = useState(false);
  const { register } = useAuthStore();
  const router = useRouter();

  const handleRegister = async () => {
    if (!form.name || !form.email || !form.password) { Alert.alert('Error', 'Please fill all fields'); return; }
    setLoading(true);
    try {
      await register(form.name, form.email, form.password, form.role);
      router.replace('/(tabs)');
    } catch (err) {
      Alert.alert('Error', err.response?.data?.detail || 'Registration failed');
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
          <Text style={{ fontSize: 26, fontWeight: '800', color: COLORS.textPrimary, marginTop: 24, marginBottom: 4 }}>Create Account</Text>
          <Text style={{ color: COLORS.textSecondary, fontSize: 15, marginBottom: 32 }}>Join NIVORA today</Text>

          <View style={{ gap: 14 }}>
            {[{ key: 'name', label: 'Full Name', placeholder: 'Your name', secure: false, keyboard: 'default', cap: 'words' },
              { key: 'email', label: 'Email Address', placeholder: 'you@example.com', secure: false, keyboard: 'email-address', cap: 'none' },
              { key: 'password', label: 'Password', placeholder: 'Min. 8 characters', secure: true, keyboard: 'default', cap: 'none' }].map((f) => (
              <View key={f.key}>
                <Text style={{ fontWeight: '600', color: COLORS.textPrimary, marginBottom: 8, fontSize: 14 }}>{f.label}</Text>
                <TextInput
                  value={form[f.key]} onChangeText={(v) => setForm({ ...form, [f.key]: v })}
                  placeholder={f.placeholder} secureTextEntry={f.secure}
                  keyboardType={f.keyboard} autoCapitalize={f.cap}
                  style={{ backgroundColor: COLORS.background, borderRadius: RADIUS.md, padding: 14, fontSize: 15, borderWidth: 1, borderColor: COLORS.border, color: COLORS.textPrimary }}
                />
              </View>
            ))}

            <View>
              <Text style={{ fontWeight: '600', color: COLORS.textPrimary, marginBottom: 8, fontSize: 14 }}>Account Type</Text>
              <View style={{ flexDirection: 'row', gap: 12 }}>
                {['CUSTOMER', 'MERCHANT'].map((role) => (
                  <TouchableOpacity key={role} onPress={() => setForm({ ...form, role })}
                    style={{ flex: 1, paddingVertical: 14, borderRadius: RADIUS.md, alignItems: 'center', backgroundColor: form.role === role ? COLORS.primary : COLORS.white, borderWidth: 1.5, borderColor: form.role === role ? COLORS.primary : COLORS.border }}
                  >
                    <Text style={{ fontWeight: '700', color: form.role === role ? 'white' : COLORS.textPrimary, fontSize: 14 }}>{role === 'CUSTOMER' ? '👤 Customer' : '🏪 Merchant'}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            <TouchableOpacity onPress={handleRegister} disabled={loading}
              style={{ backgroundColor: loading ? '#9CC4B2' : COLORS.primary, borderRadius: RADIUS.md, paddingVertical: 16, alignItems: 'center', marginTop: 8 }}
            >
              <Text style={{ color: 'white', fontWeight: '700', fontSize: 16 }}>{loading ? 'Creating...' : 'Create Account'}</Text>
            </TouchableOpacity>
          </View>

          <TouchableOpacity onPress={() => router.push('/auth/login')} style={{ alignItems: 'center', marginTop: 24 }}>
            <Text style={{ color: COLORS.textSecondary }}>Already have an account? <Text style={{ color: COLORS.primary, fontWeight: '700' }}>Sign In</Text></Text>
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
