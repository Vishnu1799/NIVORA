import 'package:flutter/material.dart';
import '../theme/colors.dart';
import 'main_navigation.dart';
import 'checkout_screen.dart';
import 'track_order_screen.dart';

class PaymentResultScreen extends StatelessWidget {
  final String transactionId;
  final Map<String, dynamic> paymentData;

  const PaymentResultScreen({
    super.key,
    required this.transactionId,
    required this.paymentData,
  });

  @override
  Widget build(BuildContext context) {
    final status = paymentData['status'] ?? 'SUCCESS';
    final failureCode = paymentData['failure_code'] ?? '';
    final isSuccess = status == 'SUCCESS';
    final isSafeReturn = status == 'SAFE_RETURN';
    final isDeclined = status == 'DECLINED';
    final isUnderVerification = status == 'UNDER_VERIFICATION';

    IconData iconData = Icons.check_circle_rounded;
    Color iconColor = AppColors.primary;
    Color iconBg = AppColors.successLight;
    String title = 'Payment Confirmed';
    String subtitle = 'Your payment was successfully verified.\nYour order is now confirmed.';

    if (isSuccess) {
      iconData = Icons.verified_rounded;
      iconColor = AppColors.primary;
      iconBg = AppColors.successLight;
      title = 'Payment Confirmed';
      subtitle = 'Your payment was successfully verified.\nYour groceries will be delivered in 10 minutes.';
    } else if (isSafeReturn) {
      iconData = Icons.shield_outlined;
      iconColor = const Color(0xFF0284C7);
      iconBg = const Color(0xFFE0F2FE);
      title = 'Payment could not be confirmed';
      subtitle = 'You do not need to make another payment.\nNo money was debited from your account (₹0).';
    } else if (isUnderVerification) {
      iconData = Icons.hourglass_top_rounded;
      iconColor = Colors.orange;
      iconBg = const Color(0xFFFFF7ED);
      title = 'Payment Under Verification';
      subtitle = 'Your payment is currently being verified. Please wait a few seconds. Do not make another payment.';
    } else if (failureCode == 'INSUFFICIENT_FUNDS' || (isDeclined && failureCode.contains('FUNDS'))) {
      iconData = Icons.account_balance_wallet_outlined;
      iconColor = Colors.redAccent;
      iconBg = AppColors.errorLight;
      title = 'Insufficient Account Balance';
      subtitle = 'Your bank declined this transaction due to low balance. ₹0 was debited. Please use another payment method.';
    } else if (failureCode == 'INVALID_DETAILS' || failureCode.contains('PIN')) {
      iconData = Icons.pin_outlined;
      iconColor = Colors.redAccent;
      iconBg = AppColors.errorLight;
      title = 'Incorrect PIN / Details';
      subtitle = 'Your bank declined this transaction due to incorrect credentials. ₹0 was debited.';
    } else if (isDeclined) {
      iconData = Icons.error_outline_rounded;
      iconColor = AppColors.error;
      iconBg = AppColors.errorLight;
      title = 'Payment Declined by Bank';
      subtitle = paymentData['failure_reason'] ?? 'The bank rejected the payment. ₹0 was debited from your account.';
    } else {
      iconData = Icons.cancel_outlined;
      iconColor = AppColors.error;
      iconBg = AppColors.errorLight;
      title = 'Payment Unsuccessful';
      subtitle = 'The transaction could not be completed. Your account was not debited.';
    }

    final orderId = '#NV${DateTime.now().millisecondsSinceEpoch.toString().substring(6)}';
    final amount = (paymentData['amount'] as num?)?.toDouble() ?? 0.0;

    return WillPopScope(
      onWillPop: () async {
        Navigator.pushAndRemoveUntil(
          context,
          MaterialPageRoute(builder: (_) => const MainNavigation(initialIndex: 0)),
          (route) => false,
        );
        return false;
      },
      child: Scaffold(
        backgroundColor: AppColors.background,
        body: SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
            child: Column(
              children: [
                const Spacer(),

                // Main Result Card
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(24),
                    boxShadow: [
                      BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 16, offset: const Offset(0, 4)),
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
                      const SizedBox(height: 8),
                      Text(
                        subtitle,
                        textAlign: TextAlign.center,
                        style: const TextStyle(fontSize: 13, color: AppColors.textSecondary, height: 1.4),
                      ),
                      const SizedBox(height: 16),

                      // Receipt Row
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

                      const SizedBox(height: 14),

                      // Guarantee Badge
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                        decoration: BoxDecoration(
                          color: isSuccess ? AppColors.primaryLight : const Color(0xFFF0F9FF),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(
                            color: isSuccess
                                ? AppColors.primary.withOpacity(0.25)
                                : const Color(0xFF0284C7).withOpacity(0.25),
                          ),
                        ),
                        child: Row(
                          children: [
                            Icon(
                              Icons.shield_rounded,
                              color: isSuccess ? AppColors.primary : const Color(0xFF0284C7),
                              size: 16,
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                isSuccess
                                    ? '✓ AUREV Verified: Zero duplicate charge risk.'
                                    : '✓ AUREV Safe Resolution: ₹0 was deducted.',
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w700,
                                  color: isSuccess ? AppColors.primaryDark : const Color(0xFF0369A1),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
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
                              transactionId: transactionId,
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
                ] else if (isSafeReturn || isDeclined) ...[
                  // Only after reaching terminal state is customer offered the option to retry with another method
                  SizedBox(
                    width: double.infinity,
                    height: 52,
                    child: ElevatedButton.icon(
                      onPressed: () {
                        Navigator.pushReplacement(
                          context,
                          MaterialPageRoute(
                            builder: (_) => const CheckoutScreen(initialMethod: 'CARD'),
                          ),
                        );
                      },
                      icon: const Icon(Icons.credit_card_rounded, color: Colors.white, size: 20),
                      label: const Text(
                        'Try With Another Payment Method',
                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.white),
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
      ),
    );
  }
}
