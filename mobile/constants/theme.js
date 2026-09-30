export const COLORS = {
  primary: '#167244',
  primaryLight: '#E8F5EE',
  primaryDark: '#0F5233',
  background: '#F5F7FA',
  white: '#FFFFFF',
  textPrimary: '#1A1A1A',
  textSecondary: '#6B7280',
  textLight: '#9CA3AF',
  border: '#E5E7EB',
  error: '#FF3B30',
  errorLight: '#FFF0EF',
  warning: '#F59E0B',
  success: '#22C55E',
  aurevDark: '#0B1F12',
  aurevDarkCard: '#122B1A',
  shadow: '#000000',
};

export const SHADOWS = {
  small: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  medium: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 4,
  },
};

export const RADIUS = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
};

export const PRODUCTS = [
  { id: '1', name: 'Fresh Apples', subtitle: '1 kg • Fresh & Juicy', price: 120, category: 'Fruits & Vegetables', unit: '1 kg', rating: 4.6, reviews: 2800, image: 'https://images.unsplash.com/photo-1567306226416-28f0efdc88ce?w=300&q=80', description: 'Premium quality fresh apples, rich in nutrients and naturally sweet. Perfect for a healthy lifestyle.' },
  { id: '2', name: 'Organic Milk', subtitle: '1 lt • Farm Fresh', price: 62, category: 'Dairy & Eggs', unit: '1 lt', rating: 4.8, reviews: 1200, image: 'https://images.unsplash.com/photo-1563636619-e9143da7973b?w=300&q=80', description: 'Pure organic milk from free-range cows. No preservatives, full cream.' },
  { id: '3', name: 'Brown Bread', subtitle: '400g • Whole Wheat', price: 45, category: 'Snacks & Breakfast', unit: '400g', rating: 4.4, reviews: 980, image: 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=300&q=80', description: 'Freshly baked whole wheat brown bread. Rich in fiber and natural goodness.' },
  { id: '4', name: 'Banana', subtitle: '1 dozen • Ripe', price: 40, category: 'Fruits & Vegetables', unit: '1 dozen', rating: 4.5, reviews: 1560, image: 'https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=300&q=80', description: 'Fresh ripe bananas, naturally sweet and rich in potassium.' },
  { id: '5', name: 'Tomato', subtitle: '500g • Farm Fresh', price: 30, category: 'Fruits & Vegetables', unit: '500g', rating: 4.3, reviews: 890, image: 'https://images.unsplash.com/photo-1546470427-e26264be0b0d?w=300&q=80', description: 'Fresh red tomatoes, rich in lycopene and natural vitamins.' },
  { id: '6', name: 'Onion', subtitle: '1 kg • Fresh', price: 40, category: 'Fruits & Vegetables', unit: '1 kg', rating: 4.2, reviews: 670, image: 'https://images.unsplash.com/photo-1518977956812-cd3dbadaaf31?w=300&q=80', description: 'Premium quality onions, essential for everyday cooking.' },
  { id: '7', name: 'Potato', subtitle: '1 kg • Fresh', price: 35, category: 'Fruits & Vegetables', unit: '1 kg', rating: 4.1, reviews: 540, image: 'https://images.unsplash.com/photo-1518977822534-7049a61ee0c2?w=300&q=80', description: 'Fresh potatoes, versatile and nutritious.' },
  { id: '8', name: 'Chicken Breast', subtitle: '500g • Boneless', price: 280, category: 'Meat & Fish', unit: '500g', rating: 4.7, reviews: 2100, image: 'https://images.unsplash.com/photo-1604503468506-a8da13d11d36?w=300&q=80', description: 'Fresh boneless chicken breast, high in protein.' },
  { id: '9', name: 'Cheddar Cheese', subtitle: '200g • Mature', price: 220, category: 'Dairy & Eggs', unit: '200g', rating: 4.6, reviews: 760, image: 'https://images.unsplash.com/photo-1618160702438-9b02ab6515c9?w=300&q=80', description: 'Rich mature cheddar cheese, perfect for sandwiches and cooking.' },
  { id: '10', name: 'Free Range Eggs', subtitle: '6 pack • Farm Fresh', price: 96, category: 'Dairy & Eggs', unit: '6 pack', rating: 4.9, reviews: 3200, image: 'https://images.unsplash.com/photo-1598965675045-45c5e72c7d05?w=300&q=80', description: 'Farm fresh free-range eggs, rich in nutrients.' },
  { id: '11', name: 'Olive Oil', subtitle: '500ml • Extra Virgin', price: 450, category: 'Cooking Essentials', unit: '500ml', rating: 4.8, reviews: 1890, image: 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=300&q=80', description: 'Premium cold-pressed extra virgin olive oil.' },
  { id: '12', name: 'Spinach', subtitle: '250g • Baby Leaves', price: 35, category: 'Fruits & Vegetables', unit: '250g', rating: 4.4, reviews: 430, image: 'https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=300&q=80', description: 'Fresh baby spinach leaves, rich in iron and vitamins.' },
];

export const CATEGORIES = [
  { id: '1', name: 'Fruits & Vegetables', desc: 'Fresh & seasonal produce', image: 'https://images.unsplash.com/photo-1610832958506-aa56368176cf?w=300&q=80' },
  { id: '2', name: 'Dairy & Eggs', desc: 'Milk, cheese, eggs & more', image: 'https://images.unsplash.com/photo-1563636619-e9143da7973b?w=300&q=80' },
  { id: '3', name: 'Snacks & Breakfast', desc: 'Biscuits, cereals, nuts', image: 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=300&q=80' },
  { id: '4', name: 'Beverages', desc: 'Tea, coffee, juices & more', image: 'https://images.unsplash.com/photo-1544145945-f90425340c7e?w=300&q=80' },
  { id: '5', name: 'Cooking Essentials', desc: 'Oils, masalas, spices', image: 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=300&q=80' },
  { id: '6', name: 'Household Essentials', desc: 'Cleaning & personal care', image: 'https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=300&q=80' },
  { id: '7', name: 'Meat & Fish', desc: 'Fresh meats & seafood', image: 'https://images.unsplash.com/photo-1604503468506-a8da13d11d36?w=300&q=80' },
  { id: '8', name: 'Baby Care', desc: 'Baby food & hygiene', image: 'https://images.unsplash.com/photo-1515488042361-ee00e0ddd4e4?w=300&q=80' },
];
