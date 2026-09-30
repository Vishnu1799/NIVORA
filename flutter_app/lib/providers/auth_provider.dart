import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_service.dart';

class AuthProvider with ChangeNotifier {
  Map<String, dynamic>? _user;
  bool _isAuthenticated = false;
  bool _initialized = false;

  Map<String, dynamic>? get user => _user;
  bool get isAuthenticated => _isAuthenticated;
  bool get initialized => _initialized;

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    final userStr = prefs.getString('nivora_user');
    if (userStr != null) {
      _user = jsonDecode(userStr);
      _isAuthenticated = true;
    }
    _initialized = true;
    notifyListeners();
  }

  Future<void> login(String email, String password) async {
    final data = await ApiService.login(email, password);
    _user = data;
    _isAuthenticated = true;
    notifyListeners();
  }

  Future<void> register(String name, String email, String password, String role) async {
    final data = await ApiService.register(name, email, password, role);
    _user = data;
    _isAuthenticated = true;
    notifyListeners();
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('nivora_token');
    await prefs.remove('nivora_user');
    _user = null;
    _isAuthenticated = false;
    notifyListeners();
  }
}
