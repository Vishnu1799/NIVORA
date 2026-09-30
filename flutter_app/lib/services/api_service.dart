import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static const String _devIp = '192.168.137.32';

  // Dynamically resolves to current host (localhost on laptop or LAN IP on mobile phone)
  static const String _envBackendUrl = String.fromEnvironment('BACKEND_URL', defaultValue: '');
  static const String _envBankUrl = String.fromEnvironment('BANK_URL', defaultValue: '');

  // Dynamically resolves to environment override, current host, or local dev port
  static String get baseUrl {
    if (_envBackendUrl.isNotEmpty) {
      return _envBackendUrl;
    }
    if (kIsWeb) {
      final host = Uri.base.host;
      if (host.isNotEmpty && host != 'localhost' && host != '127.0.0.1') {
        // If hosted on a cloud domain (e.g. vercel.app), default to matching backend host if needed
        return 'http://$host:8000';
      }
      return 'http://localhost:8000';
    }
    return 'http://10.253.25.92:8000';
  }

  static String get bankUrl {
    if (_envBankUrl.isNotEmpty) {
      return _envBankUrl;
    }
    if (kIsWeb) {
      final host = Uri.base.host;
      if (host.isNotEmpty && host != 'localhost' && host != '127.0.0.1') {
        return 'http://$host:8001';
      }
      return 'http://localhost:8001';
    }
    return 'http://10.253.25.92:8001';
  }

  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('nivora_token');
  }

  static Future<Map<String, String>> _getHeaders() async {
    final token = await getToken();
    final headers = {'Content-Type': 'application/json'};
    if (token != null) {
      headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  // AUTH
  static Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('nivora_token', data['access_token']);
      await prefs.setString('nivora_user', jsonEncode(data));
      return data;
    }
    throw Exception(jsonDecode(response.body)['detail'] ?? 'Login failed');
  }

  static Future<Map<String, dynamic>> register(String name, String email, String password, String role) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'name': name, 'email': email, 'password': password, 'role': role}),
    );
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('nivora_token', data['access_token']);
      await prefs.setString('nivora_user', jsonEncode(data));
      return data;
    }
    throw Exception(jsonDecode(response.body)['detail'] ?? 'Registration failed');
  }

  // PRODUCTS
  static Future<List<dynamic>> getProducts() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/products'));
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      debugPrint('Error loading products from backend: $e');
    }
    return [];
  }

  // ORDERS
  static Future<Map<String, dynamic>> createOrder(List<Map<String, dynamic>> items) async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('$baseUrl/api/orders'),
      headers: headers,
      body: jsonEncode({
        'items': items,
        'delivery_address': {'city': 'Bengaluru', 'pincode': '560034'},
      }),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception(jsonDecode(response.body)['detail'] ?? 'Order failed');
  }

  static Future<List<dynamic>> getOrders() async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(Uri.parse('$baseUrl/api/orders'), headers: headers);
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      debugPrint('Error getting orders: $e');
    }
    return [];
  }

  // PAYMENTS
  static Future<Map<String, dynamic>> createPayment({
    required String orderId,
    required double amount,
    required String paymentMethod,
  }) async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('$baseUrl/api/payments'),
      headers: headers,
      body: jsonEncode({
        'order_id': orderId,
        'amount': amount,
        'payment_method': paymentMethod,
        'idempotency_key': '${orderId}_${DateTime.now().millisecondsSinceEpoch}',
      }),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception(jsonDecode(response.body)['detail'] ?? 'Payment failed');
  }

  static Future<Map<String, dynamic>> getPaymentStatus(String transactionId) async {
    final headers = await _getHeaders();
    final response = await http.get(
      Uri.parse('$baseUrl/api/payments/$transactionId/status'),
      headers: headers,
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to get payment status');
  }

  static Future<List<dynamic>> getPaymentEvents(String transactionId) async {
    final headers = await _getHeaders();
    final response = await http.get(
      Uri.parse('$baseUrl/api/payments/$transactionId/events'),
      headers: headers,
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    return [];
  }

  // AUREV DASHBOARD
  static Future<Map<String, dynamic>> getAurevMetrics() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/aurev/metrics'));
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {}
    return {'bank_status': 'UP', 'auto_recovered': 0, 'successful_payments': 0};
  }

  static Future<List<dynamic>> getAurevEvents() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/aurev/events'));
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {}
    return [];
  }

  static Future<void> setBankScenario(Map<String, dynamic> payload) async {
    await http.post(
      Uri.parse('$bankUrl/admin/service-state'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(payload),
    );
  }
}
