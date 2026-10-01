import 'dart:async';
import 'package:flutter/material.dart';
import '../theme/colors.dart';
import '../services/api_service.dart';
import 'payment_result_screen.dart';

class PaymentProcessingScreen extends StatefulWidget {
  final String transactionId;
  final double amount;

  const PaymentProcessingScreen({
    super.key,
    required this.transactionId,
    required this.amount,
  });

  @override
  State<PaymentProcessingScreen> createState() => _PaymentProcessingScreenState();
}

class _PaymentProcessingScreenState extends State<PaymentProcessingScreen> with TickerProviderStateMixin {
  Timer? _timer;
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;
  String _currentStatus = 'PROCESSING';
  int _secondsWaiting = 0;

  @override
  void initState() {
    super.initState();

    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat(reverse: true);

    _pulseAnimation = Tween<double>(begin: 0.92, end: 1.08).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );

    _checkStatus();
    _startPolling();
  }

  Future<void> _checkStatus() async {
    try {
      final data = await ApiService.getPaymentStatus(widget.transactionId);
      final status = data['status'] ?? 'PROCESSING';

      if (!mounted) return;

      setState(() {
        _currentStatus = status;
      });

      if (status == 'SUCCESS' || status == 'SAFE_RETURN' || status == 'DECLINED' || status == 'FAILED') {
        _timer?.cancel();
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (_) => PaymentResultScreen(
              transactionId: widget.transactionId,
              paymentData: data,
            ),
          ),
        );
      }
    } catch (e) {
      debugPrint('Initial status check error: $e');
    }
  }

  void _startPolling() {
    // Poll every 1.0 second for rapid reaction to AUREV AI signals
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) async {
      _secondsWaiting++;
      await _checkStatus();
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isUnderVerification = _currentStatus == 'UNDER_VERIFICATION';

    return WillPopScope(
      // Prevent back gesture during active payment or verification to prevent duplicate attempts
      onWillPop: () async => false,
      child: Scaffold(
        backgroundColor: isUnderVerification ? const Color(0xFF0F172A) : AppColors.white,
        body: SafeArea(
          child: SizedBox(
            width: double.infinity,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  const Spacer(),

                  // Brand Header
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.eco_rounded,
                        color: isUnderVerification ? const Color(0xFF38BDF8) : AppColors.primary,
                        size: 32,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        'Nivora',
                        style: TextStyle(
                          fontSize: 28,
                          fontWeight: FontWeight.w800,
                          color: isUnderVerification ? Colors.white : AppColors.primary,
                          letterSpacing: -0.5,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 32),

                  // Animated Center Status Icon
                  ScaleTransition(
                    scale: _pulseAnimation,
                    child: Container(
                      width: 100,
                      height: 100,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: isUnderVerification
                            ? const Color(0xFF0369A1).withOpacity(0.3)
                            : AppColors.primaryLight,
                        border: Border.all(
                          color: isUnderVerification ? const Color(0xFF38BDF8) : AppColors.primary,
                          width: 2.5,
                        ),
                        boxShadow: isUnderVerification
                            ? [
                                BoxShadow(
                                  color: const Color(0xFF38BDF8).withOpacity(0.35),
                                  blurRadius: 24,
                                  spreadRadius: 4,
                                )
                              ]
                            : [],
                      ),
                      child: Icon(
                        isUnderVerification ? Icons.shield_rounded : Icons.sync_rounded,
                        size: 48,
                        color: isUnderVerification ? const Color(0xFF38BDF8) : AppColors.primary,
                      ),
                    ),
                  ),
                  const SizedBox(height: 32),

                  // Amount
                  Text(
                    '₹${widget.amount.toInt()}',
                    style: TextStyle(
                      fontSize: 40,
                      fontWeight: FontWeight.w900,
                      color: isUnderVerification ? Colors.white : AppColors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Primary Status Title (Exact Specification Requirement)
                  Text(
                    isUnderVerification ? 'Payment Under Verification' : 'Processing payment...',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w800,
                      color: isUnderVerification ? const Color(0xFF38BDF8) : AppColors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 12),

                  // Message (Exact Specification Requirement)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    decoration: BoxDecoration(
                      color: isUnderVerification
                          ? const Color(0xFF1E293B)
                          : const Color(0xFFF8FAFC),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(
                        color: isUnderVerification
                            ? const Color(0xFF38BDF8).withOpacity(0.3)
                            : AppColors.border,
                      ),
                    ),
                    child: Text(
                      isUnderVerification
                          ? 'Your payment is currently under verification.\nPlease wait a few seconds.\nDo not make another payment.'
                          : 'AUREV AI is securely routing your payment.\nPlease do not close this window.',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 13,
                        color: isUnderVerification ? const Color(0xFFE2E8F0) : AppColors.textSecondary,
                        height: 1.5,
                        fontWeight: isUnderVerification ? FontWeight.w600 : FontWeight.normal,
                      ),
                    ),
                  ),

                  if (isUnderVerification) ...[
                    const SizedBox(height: 20),
                    // Live verification progress indicator
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                      decoration: BoxDecoration(
                        color: const Color(0xFF0F172A),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: const Color(0xFF38BDF8).withOpacity(0.4)),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const SizedBox(
                            width: 14,
                            height: 14,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Color(0xFF38BDF8),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            'AUREV AI Autonomous Verification Active (${_secondsWaiting}s)',
                            style: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                              color: Color(0xFF38BDF8),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],

                  const Spacer(),

                  // Hard Protection Note (NO RETRY BUTTON AVAILABLE HERE)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                    decoration: BoxDecoration(
                      color: isUnderVerification ? Colors.transparent : AppColors.primaryLight,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          Icons.lock_rounded,
                          size: 14,
                          color: isUnderVerification ? const Color(0xFF94A3B8) : AppColors.primary,
                        ),
                        const SizedBox(width: 6),
                        Text(
                          isUnderVerification
                              ? 'Duplicate Charge Protection Enabled'
                              : 'Protected by AUREV AI Anti-Duplicate Layer',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                            color: isUnderVerification ? const Color(0xFF94A3B8) : AppColors.primaryDark,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
