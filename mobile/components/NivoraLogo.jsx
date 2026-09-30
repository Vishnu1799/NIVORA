import { View, Text } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../constants/theme';

export default function NivoraLogo({ size = 'md', color = COLORS.primary, dark = false }) {
  const sizes = { sm: { icon: 18, text: 16 }, md: { icon: 26, text: 22 }, lg: { icon: 38, text: 30 } };
  const s = sizes[size] || sizes.md;
  const textColor = dark ? '#FFFFFF' : color;
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
      <Ionicons name="leaf" size={s.icon} color={color} />
      <Text style={{ fontSize: s.text, fontWeight: '800', color: textColor, letterSpacing: -0.5 }}>Nivora</Text>
    </View>
  );
}
