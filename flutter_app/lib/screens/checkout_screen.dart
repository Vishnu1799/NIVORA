import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../theme/colors.dart';
import '../providers/cart_provider.dart';
import '../providers/location_provider.dart';
import '../widgets/location_picker_sheet.dart';
import '../services/api_service.dart';
import 'payment_processing_screen.dart';
import 'payment_result_screen.dart';

class CheckoutScreen extends StatefulWidget {
  final String initialMethod;
  const CheckoutScreen({super.key, this.initialMethod = 'UPI'});

  @override
  State<CheckoutScreen> createState() => _CheckoutScreenState();
}

class _CheckoutScreenState extends State<CheckoutScreen> {
  late String _selectedPaymentMethod;
  bool _isLoading = false;
  String _activeBankSignal = 'UP';
  bool _isLoadingBankSignal = false;

  @override
  void initState() {
    super.initState();
    _selectedPaymentMethod = widget.initialMethod;
    _fetchActiveBankSignal();
  }

  Future<void> _fetchActiveBankSignal() async {
    setState(() => _isLoadingBankSignal = true);
    try {
      final stateData = await ApiService.getBankState();
      final state = stateData['state'] ?? 'UP';
      final force = stateData['force_outcome'];
      final active = (force != null && force.toString().isNotEmpty) ? force.toString() : state.toString();
      if (mounted) {
        setState(() {
          _activeBankSignal = active.toUpperCase();
          _isLoadingBankSignal = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoadingBankSignal = false);
    }
  }

  String _getSignalDisplayName(String sig) {
    switch (sig) {
      case 'INSUFFICIENT_FUNDS':
      case 'FAILED':
        return '💳 Low Balance (Decline 51)';
      case 'DOWN':
        return '❌ Bank Server Down (503)';
      case 'ERROR_SIGNAL':
        return '⚡ Error Signal (Under Verification)';
      case 'TIMEOUT':
      case 'NO_RESPONSE':
        return '⏱️ Timeout (Under Verification)';
      case 'INVALID_DETAILS':
      case 'INVALID_PIN':
        return '🔑 Wrong PIN / Details (55)';
      default:
        return '🟢 Normal Operation (Success)';
    }
  }

  Color _getSignalColor(String sig) {
    switch (sig) {
      case 'INSUFFICIENT_FUNDS':
      case 'FAILED':
      case 'DOWN':
      case 'INVALID_DETAILS':
        return const Color(0xFFF87171);
      case 'ERROR_SIGNAL':
      case 'TIMEOUT':
      case 'NO_RESPONSE':
        return const Color(0xFFFBBF24);
      default:
        return const Color(0xFF34D399);
    }
  }

  void _showScenarioPickerSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => Container(
        decoration: const BoxDecoration(
          color: Color(0xFF0F172A),
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        ),
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  '⚡ AUREV Bank Simulator Signal',
                  style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 16),
                ),
                IconButton(
                  icon: const Icon(Icons.close_rounded, color: Colors.white70),
                  onPressed: () => Navigator.pop(ctx),
                ),
              ],
            ),
            const SizedBox(height: 6),
            const Text(
              'Select a bank condition to simulate for this payment test:',
              style: TextStyle(color: Color(0xFF94A3B8), fontSize: 12),
            ),
            const SizedBox(height: 16),
            _buildScenarioOption('UP', '🟢 Normal Operation', '100% successful checkout without issues', null),
            _buildScenarioOption('INSUFFICIENT_FUNDS', '💳 Low Balance (Decline 51)', 'Customer account has insufficient funds (₹0 debited)', 'INSUFFICIENT_FUNDS'),
            _buildScenarioOption('DOWN', '❌ Bank Server Down (503)', 'Core banking system offline — safe decline', null),
            _buildScenarioOption('ERROR_SIGNAL', '⚡ Trigger Error Signal', 'Drops connection mid-capture ➔ UNDER_VERIFICATION', 'ERROR_SIGNAL'),
            _buildScenarioOption('TIMEOUT', '⏱️ Trigger Timeout (504)', 'Dropped gateway reply ➔ UNDER_VERIFICATION', 'TIMEOUT'),
            _buildScenarioOption('INVALID_DETAILS', '🔑 Wrong PIN / Details (55)', 'Incorrect credentials entered (₹0 debited)', 'INVALID_DETAILS'),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Widget _buildScenarioOption(String stateKey, String title, String subtitle, String? forceOutcome) {
    final targetState = (forceOutcome ?? stateKey).toUpperCase();
    final isSelected = _activeBankSignal == targetState;
    return InkWell(
      onTap: () async {
        Navigator.pop(context);
        setState(() {
          _activeBankSignal = targetState;
        });
        await ApiService.setBankScenario({
          'state': stateKey,
          'force_outcome': forceOutcome,
          'failure_rate': 0.0,
        });
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              backgroundColor: const Color(0xFF0369A1),
              content: Text('Bank Simulator Armed: $title'),
              duration: const Duration(seconds: 2),
            ),
          );
        }
      },
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF1E293B) : const Color(0xFF131E32),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isSelected ? const Color(0xFF38BDF8) : Colors.white.withOpacity(0.08),
            width: isSelected ? 1.5 : 1,
          ),
        ),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13)),
                  const SizedBox(height: 2),
                  Text(subtitle, style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 11)),
                ],
              ),
            ),
            if (isSelected)
              const Icon(Icons.check_circle_rounded, color: Color(0xFF38BDF8), size: 20),
          ],
        ),
      ),
    );
  }

  // Credential Text Controllers
  final _upiIdController = TextEditingController(text: 'customer@okhdfcbank');
  final _upiPinController = TextEditingController(text: '7829');
  final _cardNumberController = TextEditingController(text: '4532 8921 4820 9012');
  final _cardNameController = TextEditingController(text: 'Vishnu Prashanth');
  final _cardExpiryController = TextEditingController(text: '08/29');
  final _cardCvvController = TextEditingController(text: '419');
  String _selectedBank = 'HDFC Bank';
  final _walletNumberController = TextEditingController(text: '+91 98765 43210');

  final List<Map<String, dynamic>> _paymentMethods = [
    {
      'id': 'UPI',
      'title': 'UPI Payment',
      'subtitle': 'Google Pay, PhonePe, Paytm, BHIM',
      'icon': Icons.flash_on_rounded,
    },
    {
      'id': 'CARD',
      'title': 'Credit / Debit Card',
      'subtitle': 'Visa, MasterCard, RuPay',
      'icon': Icons.credit_card_rounded,
    },
    {
      'id': 'NET_BANKING',
      'title': 'Net Banking',
      'subtitle': 'HDFC, SBI, ICICI, Axis Bank',
      'icon': Icons.account_balance_rounded,
    },
    {
      'id': 'WALLET',
      'title': 'Digital Wallet',
      'subtitle': 'Paytm, Amazon Pay, PhonePe Wallet',
      'icon': Icons.account_balance_wallet_rounded,
    },
  ];

  @override
  void dispose() {
    _upiIdController.dispose();
    _upiPinController.dispose();
    _cardNumberController.dispose();
    _cardNameController.dispose();
    _cardExpiryController.dispose();
    _cardCvvController.dispose();
    _walletNumberController.dispose();
    super.dispose();
  }

  Future<void> _handlePayNow() async {
    final cart = context.read<CartProvider>();
    if (cart.items.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please add items to your cart first.')),
      );
      return;
    }

    // Validate credentials
    if (_selectedPaymentMethod == 'UPI') {
      if (_upiIdController.text.trim().isEmpty || !_upiIdController.text.contains('@')) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Please enter a valid UPI ID (e.g. name@bank)')),
        );
        return;
      }
      if (_upiPinController.text.trim().length < 4) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Please enter your 4 or 6-digit UPI PIN')),
        );
        return;
      }
    } else if (_selectedPaymentMethod == 'CARD') {
      if (_cardNumberController.text.trim().length < 12) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Please enter a valid 16-digit Card Number')),
        );
        return;
      }
      if (_cardCvvController.text.trim().length < 3) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Please enter a valid 3-digit CVV')),
        );
        return;
      }
    }

    setState(() => _isLoading = true);

    try {
      // 1. Create Order
      final items = cart.items.map((i) => {'product_id': i.product.id, 'quantity': i.quantity}).toList();
      final order = await ApiService.createOrder(items);

      // 2. Initiate Payment with entered credentials
      final payment = await ApiService.createPayment(
        orderId: order['id'],
        amount: cart.total,
        paymentMethod: _selectedPaymentMethod,
      );

      final transactionId = payment['transaction_id'] ?? 'TXN_${DateTime.now().millisecondsSinceEpoch}';
      final status = payment['status'] ?? 'PROCESSING';
      final amount = cart.total;
      cart.clearCart();

      if (!mounted) return;

      if (status == 'DECLINED' || status == 'SAFE_RETURN') {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (_) => PaymentResultScreen(
              transactionId: transactionId,
              paymentData: payment,
            ),
          ),
        );
      } else {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (_) => PaymentProcessingScreen(
              transactionId: transactionId,
              amount: amount,
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            backgroundColor: AppColors.error,
            content: Text('Payment Error: ${e.toString().replaceAll('Exception: ', '')}'),
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Widget _buildCredentialInputs() {
    if (_selectedPaymentMethod == 'UPI') {
      return Container(
        margin: const EdgeInsets.only(top: 10),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.primaryLight.withOpacity(0.4),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.primary.withOpacity(0.25)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Enter UPI Details', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppColors.primaryDark)),
            const SizedBox(height: 10),
            TextField(
              controller: _upiIdController,
              decoration: InputDecoration(
                labelText: 'UPI ID / VPA',
                hintText: 'yourname@okhdfcbank',
                prefixIcon: const Icon(Icons.alternate_email_rounded, size: 20, color: AppColors.primary),
                filled: true,
                fillColor: Colors.white,
                contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
              ),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _upiPinController,
              obscureText: true,
              keyboardType: TextInputType.number,
              decoration: InputDecoration(
                labelText: 'UPI PIN (4 or 6-digit)',
                hintText: '••••',
                prefixIcon: const Icon(Icons.lock_outline_rounded, size: 20, color: AppColors.primary),
                filled: true,
                fillColor: Colors.white,
                contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
              ),
            ),
          ],
        ),
      );
    }

    if (_selectedPaymentMethod == 'CARD') {
      return Container(
        margin: const EdgeInsets.only(top: 10),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.primaryLight.withOpacity(0.4),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.primary.withOpacity(0.25)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Enter Card Details', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppColors.primaryDark)),
            const SizedBox(height: 10),
            TextField(
              controller: _cardNumberController,
              keyboardType: TextInputType.number,
              decoration: InputDecoration(
                labelText: 'Card Number',
                hintText: '4532 8921 4820 9012',
                prefixIcon: const Icon(Icons.credit_card_rounded, size: 20, color: AppColors.primary),
                filled: true,
                fillColor: Colors.white,
                contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
              ),
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _cardExpiryController,
                    decoration: InputDecoration(
                      labelText: 'Expiry (MM/YY)',
                      hintText: '08/29',
                      filled: true,
                      fillColor: Colors.white,
                      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: TextField(
                    controller: _cardCvvController,
                    obscureText: true,
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(
                      labelText: 'CVV',
                      hintText: '419',
                      filled: true,
                      fillColor: Colors.white,
                      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      );
    }

    if (_selectedPaymentMethod == 'NET_BANKING') {
      return Container(
        margin: const EdgeInsets.only(top: 10),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.primaryLight.withOpacity(0.4),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.primary.withOpacity(0.25)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Select Your Bank', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppColors.primaryDark)),
            const SizedBox(height: 10),
            DropdownButtonFormField<String>(
              value: _selectedBank,
              items: ['HDFC Bank', 'State Bank of India', 'ICICI Bank', 'Axis Bank', 'Kotak Mahindra']
                  .map((b) => DropdownMenuItem(value: b, child: Text(b)))
                  .toList(),
              onChanged: (val) => setState(() => _selectedBank = val!),
              decoration: InputDecoration(
                filled: true,
                fillColor: Colors.white,
                contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
              ),
            ),
          ],
        ),
      );
    }

    return Container(
      margin: const EdgeInsets.only(top: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.primaryLight.withOpacity(0.4),
        borderRadius: BorderRadius.circular(12),
      ),
      child: TextField(
        controller: _walletNumberController,
        keyboardType: TextInputType.phone,
        decoration: InputDecoration(
          labelText: 'Linked Mobile Number',
          filled: true,
          fillColor: Colors.white,
          contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final cart = context.watch<CartProvider>();
    final location = context.watch<LocationProvider>();

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded, color: AppColors.textPrimary),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text('Checkout & Payment', style: TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.w800)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Delivery Address Card
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(14),
                boxShadow: [
                  BoxShadow(color: Colors.black.withOpacity(0.03), blurRadius: 6, offset: const Offset(0, 2)),
                ],
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.location_on_rounded, color: AppColors.primary, size: 22),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Text(
                              'Delivery Address (${location.currentAddress.title})',
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                            ),
                            const SizedBox(width: 6),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                              decoration: BoxDecoration(
                                color: AppColors.primaryLight,
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text(
                                '⚡ ${location.currentAddress.deliveryTime}',
                                style: const TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: AppColors.primaryDark),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 3),
                        Text(
                          location.currentAddress.address,
                          style: const TextStyle(color: AppColors.textSecondary, fontSize: 12, height: 1.4),
                        ),
                      ],
                    ),
                  ),
                  TextButton(
                    onPressed: () => LocationPickerSheet.show(context),
                    child: const Text('Change', style: TextStyle(color: AppColors.primary, fontWeight: FontWeight.bold, fontSize: 13)),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 14),

            // Live Bank Signal / Simulation Card
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
              decoration: BoxDecoration(
                color: const Color(0xFF0F172A),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: const Color(0xFF38BDF8).withOpacity(0.35)),
                boxShadow: [
                  BoxShadow(color: const Color(0xFF38BDF8).withOpacity(0.12), blurRadius: 10, offset: const Offset(0, 2)),
                ],
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: const Color(0xFF1E293B),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Icon(Icons.hub_rounded, color: Color(0xFF38BDF8), size: 18),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            const Text(
                              'AUREV Bank Switch Simulator',
                              style: TextStyle(color: Color(0xFF94A3B8), fontSize: 11, fontWeight: FontWeight.w600),
                            ),
                            if (_isLoadingBankSignal) ...[
                              const SizedBox(width: 6),
                              const SizedBox(width: 10, height: 10, child: CircularProgressIndicator(strokeWidth: 1.5, color: Color(0xFF38BDF8))),
                            ],
                          ],
                        ),
                        const SizedBox(height: 2),
                        Text(
                          _getSignalDisplayName(_activeBankSignal),
                          style: TextStyle(
                            color: _getSignalColor(_activeBankSignal),
                            fontSize: 13,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ],
                    ),
                  ),
                  ElevatedButton.icon(
                    onPressed: _showScenarioPickerSheet,
                    icon: const Icon(Icons.tune_rounded, size: 13, color: Colors.white),
                    label: const Text('Simulate', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.white)),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF0369A1),
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      minimumSize: Size.zero,
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 16),

            // Payment Method Selection & Inputs
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(color: Colors.black.withOpacity(0.03), blurRadius: 6, offset: const Offset(0, 2)),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Payment Method & Credentials', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
                  const SizedBox(height: 10),
                  ..._paymentMethods.map((method) {
                    final isSelected = _selectedPaymentMethod == method['id'];
                    return Column(
                      children: [
                        InkWell(
                          onTap: () => setState(() => _selectedPaymentMethod = method['id']),
                          child: Padding(
                            padding: const EdgeInsets.symmetric(vertical: 8),
                            child: Row(
                              children: [
                                Icon(
                                  isSelected ? Icons.radio_button_checked_rounded : Icons.radio_button_off_rounded,
                                  color: isSelected ? AppColors.primary : AppColors.textLight,
                                  size: 20,
                                ),
                                const SizedBox(width: 10),
                                Icon(method['icon'] as IconData, color: isSelected ? AppColors.primary : AppColors.textLight, size: 22),
                                const SizedBox(width: 10),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        method['title'],
                                        style: TextStyle(
                                          fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                                          fontSize: 14,
                                          color: AppColors.textPrimary,
                                        ),
                                      ),
                                      Text(
                                        method['subtitle'],
                                        style: const TextStyle(fontSize: 11, color: AppColors.textLight),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                        if (isSelected) _buildCredentialInputs(),
                        const Divider(height: 16, color: AppColors.border),
                      ],
                    );
                  }),
                ],
              ),
            ),

            const SizedBox(height: 16),

            // Order Summary
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Items Subtotal', style: TextStyle(color: AppColors.textSecondary, fontSize: 14)),
                      Text('₹${cart.subtotal.toInt()}', style: const TextStyle(fontWeight: FontWeight.bold)),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Delivery Fee', style: TextStyle(color: AppColors.textSecondary, fontSize: 14)),
                      Text('₹${cart.deliveryFee.toInt()}', style: const TextStyle(fontWeight: FontWeight.bold)),
                    ],
                  ),
                  const Divider(height: 20, color: AppColors.border),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Total Payable', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
                      Text('₹${cart.total.toInt()}', style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 20, color: AppColors.primary)),
                    ],
                  ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            // Pay Now CTA Button
            SizedBox(
              width: double.infinity,
              height: 54,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _handlePayNow,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  elevation: 0,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                ),
                child: _isLoading
                    ? const SizedBox(
                        width: 24,
                        height: 24,
                        child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2.5),
                      )
                    : Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.lock_outline_rounded, color: Colors.white, size: 18),
                          const SizedBox(width: 8),
                          Text(
                            'Authorize & Pay ₹${cart.total.toInt()}',
                            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                          ),
                        ],
                      ),
              ),
            ),
            const SizedBox(height: 12),
            Center(
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: const [
                  Icon(Icons.verified_user_outlined, size: 14, color: AppColors.textLight),
                  SizedBox(width: 6),
                  Text('100% Secure 256-Bit SSL Encrypted & AUREV Protected', style: TextStyle(fontSize: 11, color: AppColors.textLight)),
                ],
              ),
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }
}
