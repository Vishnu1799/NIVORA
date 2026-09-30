import 'package:flutter/material.dart';

class SavedAddress {
  final String id;
  final String title;
  final String address;
  final String deliveryTime;
  final IconData icon;

  SavedAddress({
    required this.id,
    required this.title,
    required this.address,
    required this.deliveryTime,
    required this.icon,
  });
}

class LocationProvider extends ChangeNotifier {
  SavedAddress _currentAddress = SavedAddress(
    id: '1',
    title: 'Home',
    address: '12, Green Park, 3rd Cross, Koramangala, Bangalore - 560034',
    deliveryTime: '10 MINS',
    icon: Icons.home_rounded,
  );

  final List<SavedAddress> _savedAddresses = [
    SavedAddress(
      id: '1',
      title: 'Home',
      address: '12, Green Park, 3rd Cross, Koramangala, Bangalore - 560034',
      deliveryTime: '10 MINS',
      icon: Icons.home_rounded,
    ),
    SavedAddress(
      id: '2',
      title: 'Work / Office',
      address: 'WeWork Galaxy, 43 Residency Road, Shanthala Nagar, Bangalore - 560025',
      deliveryTime: '8 MINS',
      icon: Icons.work_rounded,
    ),
    SavedAddress(
      id: '3',
      title: 'Parents House',
      address: '45, 14th Main Rd, Sector 4, HSR Layout, Bangalore - 560102',
      deliveryTime: '12 MINS',
      icon: Icons.family_restroom_rounded,
    ),
    SavedAddress(
      id: '4',
      title: 'Gym / Fitness',
      address: '100 Feet Rd, HAL 2nd Stage, Indiranagar, Bangalore - 560038',
      deliveryTime: '15 MINS',
      icon: Icons.fitness_center_rounded,
    ),
  ];

  SavedAddress get currentAddress => _currentAddress;
  List<SavedAddress> get savedAddresses => _savedAddresses;

  void selectAddress(SavedAddress address) {
    _currentAddress = address;
    notifyListeners();
  }

  void addCustomAddress(String title, String fullAddress, String time) {
    final newAddress = SavedAddress(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      title: title,
      address: fullAddress,
      deliveryTime: time,
      icon: Icons.location_on_rounded,
    );
    _savedAddresses.add(newAddress);
    _currentAddress = newAddress;
    notifyListeners();
  }
}
