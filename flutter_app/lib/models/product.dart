class Product {
  final String id;
  final String name;
  final String subtitle;
  final double price;
  final double originalPrice;
  final int discountPercent;
  final String category;
  final String unit;
  final double rating;
  final int reviews;
  final String imageUrl;
  final String description;
  final String badge;
  final bool isOrganic;

  Product({
    required this.id,
    required this.name,
    required this.subtitle,
    required this.price,
    this.originalPrice = 0.0,
    this.discountPercent = 0,
    required this.category,
    required this.unit,
    required this.rating,
    required this.reviews,
    required this.imageUrl,
    required this.description,
    this.badge = 'Fresh',
    this.isOrganic = false,
  });

  factory Product.fromJson(Map<String, dynamic> json) {
    final price = (json['price'] as num?)?.toDouble() ?? 0.0;
    return Product(
      id: json['id']?.toString() ?? '',
      name: json['name'] ?? '',
      subtitle: '${json['unit'] ?? ''} • Fresh & Natural',
      price: price,
      originalPrice: price * 1.25,
      discountPercent: 20,
      category: json['category'] ?? 'General',
      unit: json['unit'] ?? '1 pc',
      rating: 4.8,
      reviews: 1850,
      imageUrl: json['image_url'] ?? 'https://images.unsplash.com/photo-1610832958506-aa56368176cf?w=300&q=80',
      description: json['description'] ?? 'Farm fresh premium grocery handpicked daily.',
      badge: 'Bestseller',
      isOrganic: true,
    );
  }
}

class CategoryItem {
  final String id;
  final String name;
  final String desc;
  final String imageUrl;
  final String iconCode;

  CategoryItem({
    required this.id,
    required this.name,
    required this.desc,
    required this.imageUrl,
    this.iconCode = 'eco',
  });
}

final List<Product> mockProducts = [
  Product(
    id: '1',
    name: 'Fresh Apples (Royal Gala)',
    subtitle: '1 kg • Crisp & Sweet',
    price: 120.0,
    originalPrice: 160.0,
    discountPercent: 25,
    category: 'Fruits & Vegetables',
    unit: '1 kg',
    rating: 4.8,
    reviews: 2840,
    imageUrl: 'https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=500&q=80',
    description: 'Crisp, sweet, and juicy Royal Gala apples sourced directly from Himachal orchards. Rich in antioxidants and dietary fiber.',
    badge: 'Trending',
    isOrganic: true,
  ),
  Product(
    id: '2',
    name: 'Organic Full Cream Milk',
    subtitle: '1 lt • Farm Fresh Daily',
    price: 62.0,
    originalPrice: 70.0,
    discountPercent: 11,
    category: 'Dairy & Eggs',
    unit: '1 lt',
    rating: 4.9,
    reviews: 3420,
    imageUrl: 'https://images.unsplash.com/photo-1550583724-b2692b85b150?w=500&q=80',
    description: 'Fresh farm-sourced organic whole milk. Free of antibiotics, preservatives, and artificial hormones.',
    badge: 'Daily Need',
    isOrganic: true,
  ),
  Product(
    id: '3',
    name: 'Artisan Whole Wheat Bread',
    subtitle: '400g • Freshly Baked',
    price: 45.0,
    originalPrice: 55.0,
    discountPercent: 18,
    category: 'Snacks & Breakfast',
    unit: '400g',
    rating: 4.6,
    reviews: 1120,
    imageUrl: 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500&q=80',
    description: '100% whole wheat artisanal bread baked every morning. Zero maida, zero palm oil.',
    badge: 'Freshly Baked',
  ),
  Product(
    id: '4',
    name: 'Robusta Golden Bananas',
    subtitle: '1 dozen • Naturally Ripe',
    price: 40.0,
    originalPrice: 50.0,
    discountPercent: 20,
    category: 'Fruits & Vegetables',
    unit: '1 dozen',
    rating: 4.7,
    reviews: 2180,
    imageUrl: 'https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=500&q=80',
    description: 'Naturally ripened Robusta bananas packed with potassium and essential vitamins.',
    badge: 'Super Saver',
  ),
  Product(
    id: '5',
    name: 'Organic Vine Ripe Tomatoes',
    subtitle: '500g • Sweet & Tangy',
    price: 30.0,
    originalPrice: 42.0,
    discountPercent: 28,
    category: 'Fruits & Vegetables',
    unit: '500g',
    rating: 4.5,
    reviews: 950,
    imageUrl: 'https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=500&q=80',
    description: 'Plump and juicy vine-ripened organic tomatoes, rich in lycopene and vitamin C.',
    badge: 'Farm Fresh',
    isOrganic: true,
  ),
  Product(
    id: '6',
    name: 'Fresh Red Onions (Nasik)',
    subtitle: '1 kg • Sharp & Flavorful',
    price: 40.0,
    originalPrice: 52.0,
    discountPercent: 23,
    category: 'Fruits & Vegetables',
    unit: '1 kg',
    rating: 4.6,
    reviews: 1670,
    imageUrl: 'https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?w=500&q=80',
    description: 'Premium quality Nasik red onions, perfect for Indian curries and salads.',
  ),
  Product(
    id: '7',
    name: 'Organic Gold Potatoes',
    subtitle: '1 kg • Naturally Grown',
    price: 35.0,
    originalPrice: 45.0,
    discountPercent: 22,
    category: 'Fruits & Vegetables',
    unit: '1 kg',
    rating: 4.4,
    reviews: 840,
    imageUrl: 'https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=500&q=80',
    description: 'Thin-skinned golden potatoes, ideal for roasting, baking, or Indian subzis.',
  ),
  Product(
    id: '8',
    name: 'Farm Fresh Brown Eggs',
    subtitle: '6 pack • Free Range & Grain Fed',
    price: 96.0,
    originalPrice: 120.0,
    discountPercent: 20,
    category: 'Dairy & Eggs',
    unit: '6 pack',
    rating: 4.9,
    reviews: 4120,
    imageUrl: 'https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=500&q=80',
    description: 'Cage-free brown eggs from healthy grain-fed hens. Rich in protein, Omega-3, and lutein.',
    badge: 'Top Pick',
  ),
  Product(
    id: '9',
    name: 'Cold-Pressed Extra Virgin Olive Oil',
    subtitle: '500ml • First Cold Press',
    price: 450.0,
    originalPrice: 580.0,
    discountPercent: 22,
    category: 'Cooking Essentials',
    unit: '500ml',
    rating: 4.9,
    reviews: 1980,
    imageUrl: 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=500&q=80',
    description: 'Single-estate extra virgin olive oil cold-pressed within 24 hours of harvest.',
    badge: 'Gourmet',
    isOrganic: true,
  ),
  Product(
    id: '10',
    name: 'Fresh Baby Spinach Leaves',
    subtitle: '250g • Hydroponic Clean',
    price: 35.0,
    originalPrice: 48.0,
    discountPercent: 27,
    category: 'Fruits & Vegetables',
    unit: '250g',
    rating: 4.7,
    reviews: 670,
    imageUrl: 'https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=500&q=80',
    description: 'Crisp, washed, and ready-to-eat baby spinach leaves packed with iron and folate.',
    badge: 'Hydroponic',
    isOrganic: true,
  ),
  Product(
    id: '11',
    name: 'A2 Malai Paneer (Fresh Cubes)',
    subtitle: '200g • Soft & Creamy',
    price: 110.0,
    originalPrice: 135.0,
    discountPercent: 18,
    category: 'Dairy & Eggs',
    unit: '200g',
    rating: 4.8,
    reviews: 2190,
    imageUrl: 'https://images.unsplash.com/photo-1559561853-08451507cbe7?w=500&q=80',
    description: 'Traditional handcrafted malai paneer made from pure cow milk. Ultra soft and melt-in-mouth texture.',
    badge: 'Bestseller',
  ),
  Product(
    id: '12',
    name: 'California Almonds (Raw & Crunchy)',
    subtitle: '250g • High Protein',
    price: 240.0,
    originalPrice: 310.0,
    discountPercent: 22,
    category: 'Snacks & Breakfast',
    unit: '250g',
    rating: 4.9,
    reviews: 1450,
    imageUrl: 'https://images.unsplash.com/photo-1508061253366-f7da158b6d46?w=400&q=80',
    description: 'Hand-selected premium California almonds, rich in Vitamin E, magnesium, and dietary fiber.',
    badge: 'Superfood',
  ),
];

final List<CategoryItem> mockCategories = [
  CategoryItem(
    id: '1',
    name: 'Fruits & Vegetables',
    desc: 'Fresh farm produce',
    imageUrl: 'https://images.unsplash.com/photo-1610832958506-aa56368176cf?w=300&q=80',
    iconCode: 'eco',
  ),
  CategoryItem(
    id: '2',
    name: 'Dairy & Eggs',
    desc: 'Milk, cheese, eggs',
    imageUrl: 'https://images.unsplash.com/photo-1563636619-e9143da7973b?w=300&q=80',
    iconCode: 'local_drink',
  ),
  CategoryItem(
    id: '3',
    name: 'Snacks & Breakfast',
    desc: 'Breads, nuts, cereals',
    imageUrl: 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=300&q=80',
    iconCode: 'bakery_dining',
  ),
  CategoryItem(
    id: '4',
    name: 'Cooking Essentials',
    desc: 'Oils, masalas, spices',
    imageUrl: 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=300&q=80',
    iconCode: 'soup_kitchen',
  ),
  CategoryItem(
    id: '5',
    name: 'Beverages',
    desc: 'Juices, tea, coffee',
    imageUrl: 'https://images.unsplash.com/photo-1544145945-f90425340c7e?w=300&q=80',
    iconCode: 'coffee',
  ),
  CategoryItem(
    id: '6',
    name: 'Household Essentials',
    desc: 'Cleaning & hygiene',
    imageUrl: 'https://images.unsplash.com/photo-1585771724684-38269d6639fd?w=300&q=80',
    iconCode: 'cleaning_services',
  ),
];
