import 'package:flutter/material.dart';
import '../theme/colors.dart';
import '../services/api_service.dart';
import 'main_navigation.dart';
import 'checkout_screen.dart';
import 'track_order_screen.dart';

class PaymentResultScreen extends StatefulWidget {
  final String transactionId;
  final Map<String, dynamic> paymentData;

  const PaymentResultScreen({
    super.key,
    required this.transactionId,
    required this.paymentData,
  });

  @override
  State<PaymentResultScreen> createState() => _PaymentResultScreenState();
}

class _PaymentResultScreenState extends State<PaymentResultScreen> {
  late Map<String, dynamic> _currentPaymentData;
  bool _isCheckingStatus = false;

  @override
  void initState() {
    super.initState();
    _currentPaymentData = Map<String, dynamic>.from(widget.paymentData);
  }

  Future<void> _checkStatusAgain() async {
    setState(() => _isCheckingStatus = true);
    try {
      final data = await ApiService.getPaymentStatus(widget.transactionId);
      if (data != null && mounted) {
        setState(() {
          _currentPaymentData = data;
        });
      }
    } catch (_) {}
    if (mounted) setState(() => _isCheckingStatus = false);
  }

  @override
  Widget build(BuildContext context) {
    final status = _currentPaymentData['status'] ?? 'SUCCESS';
    final recoveryCount = _currentPaymentData['recovery_attempt_count'] ?? 0;
    final failureCode = _currentPaymentData['failure_code'] ?? '';
    final isSuccess = status == 'SUCCESS';
    final wasRecovered = isSuccess && recoveryCount > 0;
    final isDeclined = status == 'DECLINED';
    final isEscalated = status == 'ESCALATED' || status == 'UNKNOWN' || status == 'RECONCILING';

    IconData iconData = Icons.check_circle_rounded;
    Color iconColor = AppColors.primary;
    Color iconBg = AppColors.successLight;
    String title = 'Order Placed Successfully!';
    String subtitle = 'Your groceries will be delivered in 10 minutes.';

    // Safest fallback method recommendation
    String recommendedMethod = 'CARD';
    String recommendedMethodLabel = 'Credit / Debit Card';
    IconData recommendedMethodIcon = Icons.credit_card_rounded;

    if (wasRecovered) {
      iconData = Icons.verified_rounded;
      iconColor = AppColors.primary;
      iconBg = AppColors.successLight;
      title = 'Order Placed Successfully!';
      subtitle = 'Network delay was resolved automatically. Your order is confirmed and will arrive in 10 minutes.';
    } else if (failureCode == 'INSUFFICIENT_FUNDS' || (isDeclined && failureCode.contains('FUNDS'))) {
      iconData = Icons.account_balance_wallet_outlined;
      iconColor = Colors.redAccent;
      iconBg = AppColors.errorLight;
      title = 'Insufficient Account Balance';
      subtitle = 'Your bank declined this transaction due to low balance. ₹0 was debited. Please use another payment option.';
      recommendedMethod = 'CARD';
      recommendedMethodLabel = 'Credit / Debit Card';
      recommendedMethodIcon = Icons.credit_card_rounded;
    } else if (failureCode == 'INVALID_DETAILS' || failureCode.contains('PIN')) {
      iconData = Icons.pin_outlined;
      iconColor = Colors.redAccent;
      iconBg = AppColors.errorLight;
      title = 'Incorrect PIN / Details';
      subtitle = 'Your bank declined this transaction due to incorrect credentials. ₹0 was debited. Please re-enter credentials.';
      recommendedMethod = 'UPI';
      recommendedMethodLabel = 'UPI via Google Pay / PhonePe';
      recommendedMethodIcon = Icons.flash_on_rounded;
    } else if (failureCode == 'BANK_UNAVAILABLE' || (isDeclined && failureCode.contains('BANK'))) {
      iconData = Icons.cloud_off_rounded;
      iconColor = Colors.redAccent;
      iconBg = AppColors.errorLight;
      title = 'Bank Service Unavailable';
      subtitle = 'Your bank is temporarily offline for maintenance. ₹0 was debited. Please use another bank or card.';
      recommendedMethod = 'CARD';
      recommendedMethodLabel = 'Card / Nivora Instant Wallet';
      recommendedMethodIcon = Icons.credit_card_rounded;
    } else if (isDeclined) {
      iconData = Icons.error_outline_rounded;
      iconColor = AppColors.error;
      iconBg = AppColors.errorLight;
      title = 'Payment Declined by Bank';
      subtitle = _currentPaymentData['failure_reason'] ?? 'The bank rejected the payment. ₹0 was debited from your account.';
    } else if (isEscalated) {
      iconData = Icons.lock_clock_rounded;
      iconColor = Colors.orange;
      iconBg = const Color(0xFFFFF7ED);
      title = 'Payment Under Verification';
      subtitle = 'We are verifying the transaction with your bank. If money was debited, your order will confirm automatically without double charge.';
    } else if (!isSuccess) {
      iconData = Icons.cancel_outlined;
      iconColor = AppColors.error;
      iconBg = AppColors.errorLight;
      title = 'Payment Unsuccessful';
      subtitle = 'The transaction could not be completed. Your account was not debited.';
    }

    final orderId = '#NV${DateTime.now().millisecondsSinceEpoch.toString().substring(6)}';
    final amount = (_currentPaymentData['amount'] as num?)?.toDouble() ?? 485.0;

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          child: Column(
            children: [
              const Spacer(),

              // Main Clean Card
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(24),
                  boxShadow: [
                    BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 16, offset: const Offset(0, 4)),
                  ],
                ),
                child: Column(
                  children: [
                    Container(
                      width: 72,
                      height: 72,
                      decoration: BoxDecoration(
                        color: iconBg,
                        shape: BoxShape.circle,
                      ),
                      child: Icon(iconData, color: iconColor, size: 40),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      title,
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: AppColors.textPrimary),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      subtitle,
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontSize: 12, color: AppColors.textSecondary, height: 1.4),
                    ),
                    const SizedBox(height: 16),

                    // Clean Receipt Summary
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                      decoration: BoxDecoration(
                        color: AppColors.background,
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('Order ID', style: TextStyle(fontSize: 11, color: AppColors.textLight)),
                              const SizedBox(height: 2),
                              Text(orderId, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
                            ],
                          ),
                          if (amount > 0)
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                Text(isSuccess ? 'Total Paid' : 'Amount', style: const TextStyle(fontSize: 11, color: AppColors.textLight)),
                                const SizedBox(height: 2),
                                Text('₹${amount.toInt()}', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900, color: isSuccess ? AppColors.primary : AppColors.textPrimary)),
                              ],
                            ),
                        ],
                      ),
                    ),

                    if (wasRecovered || isSuccess) ...[
                      const SizedBox(height: 12),
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                        decoration: BoxDecoration(
                          color: AppColors.primaryLight,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: AppColors.primary.withOpacity(0.2)),
                        ),
                        child: Row(
                          children: const [
                            Icon(Icons.shield_rounded, color: AppColors.primary, size: 16),
                            SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                '✓ 100% Safe Payment Guarantee: Zero duplicate charges.',
                                style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppColors.primaryDark),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ] else if (isEscalated) ...[
                      const SizedBox(height: 12),
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                        decoration: BoxDecoration(
                          color: Colors.amber.shade50,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: Colors.amber.shade300),
                        ),
                        child: Row(
                          children: const [
                            Icon(Icons.lock_rounded, color: Colors.orange, size: 16),
                            SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                '🔒 Payment Verification in Progress: Please wait a moment before trying again.',
                                style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: Color(0xFF9A3412)),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ] else if (isDeclined || !isSuccess) ...[
                      // SMART NEXT SAFEST ROUTING CARD
                      const SizedBox(height: 12),
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: const Color(0xFFF0FDF4),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: AppColors.primary.withOpacity(0.3)),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: const [
                                Icon(Icons.shield_outlined, color: AppColors.primary, size: 16),
                                SizedBox(width: 6),
                                Text(
                                  'Recommended Safe Next Step',
                                  style: TextStyle(fontWeight: FontWeight.w800, fontSize: 11, color: AppColors.primaryDark),
                                ),
                              ],
                            ),
                            const SizedBox(height: 4),
                            Text(
                              '• No money was debited from your account (₹0).\n• Recommended alternative: $recommendedMethodLabel.\n• Safe to checkout with zero duplicate charge risk.',
                              style: const TextStyle(fontSize: 10, color: AppColors.textSecondary, height: 1.4),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ],
                ),
              ),

              const Spacer(),

              // Action Buttons
              if (isSuccess) ...[
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: ElevatedButton(
                    onPressed: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => TrackOrderScreen(
                            orderId: orderId,
                            totalAmount: amount,
                            transactionId: widget.transactionId,
                          ),
                        ),
                      );
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      elevation: 0,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                    ),
                    child: const Text('Track Delivery (10 Min)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Colors.white)),
                  ),
                ),
                const SizedBox(height: 10),
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: OutlinedButton(
                    onPressed: () {
                      Navigator.pushAndRemoveUntil(
                        context,
                        MaterialPageRoute(builder: (_) => const MainNavigation(initialIndex: 0)),
                        (route) => false,
                      );
                    },
                    style: OutlinedButton.styleFrom(
                      side: const BorderSide(color: AppColors.border, width: 1.5),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                    ),
                    child: const Text('Continue Shopping', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppColors.textPrimary)),
                  ),
                ),
              ] else if (isEscalated) ...[
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: ElevatedButton.icon(
                    onPressed: _isCheckingStatus ? null : _checkStatusAgain,
                    icon: _isCheckingStatus
                        ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                        : const Icon(Icons.sync_rounded, color: Colors.white, size: 18),
                    label: Text(
                      _isCheckingStatus ? 'Verifying with Bank...' : 'Check Payment Status',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.white),
                    ),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      elevation: 0,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                    ),
                  ),
                ),
                const SizedBox(height: 10),
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: OutlinedButton(
                    onPressed: () {
                      Navigator.pushAndRemoveUntil(
                        context,
                        MaterialPageRoute(builder: (_) => const MainNavigation(initialIndex: 0)),
                        (route) => false,
                      );
                    },
                    style: OutlinedButton.styleFrom(
                      side: const BorderSide(color: AppColors.border, width: 1.5),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                    ),
                    child: const Text('Return to Home', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppColors.textPrimary)),
                  ),
                ),
              ] else ...[
                // FIRST ATTEMPT FAILED: Guide user directly to the second safest route without duplicate charge risk
                SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: ElevatedButton.icon(
                    onPressed: () {
                      Navigator.pushReplacement(
                        context,
                        MaterialPageRoute(
                          builder: (_) => CheckoutScreen(initialMethod: recommendedMethod),
                        ),
                      );
                    },
                    icon: Icon(recommendedMethodIcon, color: Colors.white, size: 20),
                    label: Text(
                      'Pay via $recommendedMethodLabel',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.white),
                    ),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      elevation: 0,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                    ),
                  ),
                ),
                const SizedBox(height: 10),
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: OutlinedButton(
                    onPressed: () {
                      Navigator.pushAndRemoveUntil(
                        context,
                        MaterialPageRoute(builder: (_) => const MainNavigation(initialIndex: 0)),
                        (route) => false,
                      );
                    },
                    style: OutlinedButton.styleFrom(
                      side: const BorderSide(color: AppColors.border, width: 1.5),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                    ),
                    child: const Text('Return to Home (Cart Saved)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppColors.textPrimary)),
                  ),
                ),
              ],
              const SizedBox(height: 10),
            ],
          ),
        ),
      ),
    );
  }
}
