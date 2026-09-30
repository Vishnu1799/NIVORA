import 'dart:async';
import 'package:flutter/material.dart';
import '../theme/colors.dart';
import '../services/api_service.dart';
import 'payment_result_screen.dart';
import 'aurev_analysis_screen.dart';

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
  late List<AnimationController> _dotControllers;

  @override
  void initState() {
    super.initState();

    _dotControllers = List.generate(
      3,
      (index) => AnimationController(
        vsync: this,
        duration: const Duration(milliseconds: 600),
      )..repeat(reverse: true),
    );

    // Stagger dots
    Future.delayed(const Duration(milliseconds: 200), () {
      if (mounted) _dotControllers[1].repeat(reverse: true);
    });
    Future.delayed(const Duration(milliseconds: 400), () {
      if (mounted) _dotControllers[2].repeat(reverse: true);
    });

    _startPolling();
  }

  void _startPolling() {
    _timer = Timer.periodic(const Duration(seconds: 2), (timer) async {
      try {
        final data = await ApiService.getPaymentStatus(widget.transactionId);
        final status = data['status'];

        if (status == 'FAILED') {
          timer.cancel();
          if (!mounted) return;
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(
              builder: (_) => AurevAnalysisScreen(transactionId: widget.transactionId),
            ),
          );
        } else if (['SUCCESS', 'DECLINED', 'ESCALATED', 'UNKNOWN'].contains(status)) {
          timer.cancel();
          if (!mounted) return;
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
        debugPrint('Polling error: $e');
      }
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    for (var c in _dotControllers) {
      c.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.white,
      body: SafeArea(
        child: SizedBox(
          width: double.infinity,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              const Spacer(),
              // Nivora Brand
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: const [
                  Icon(Icons.eco_rounded, color: AppColors.primary, size: 32),
                  SizedBox(width: 8),
                  Text(
                    'Nivora',
                    style: TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.w800,
                      color: AppColors.primary,
                      letterSpacing: -0.5,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 36),

              // Amount
              Text(
                '₹${widget.amount.toInt()}',
                style: const TextStyle(fontSize: 44, fontWeight: FontWeight.w900, color: AppColors.textPrimary),
              ),
              const SizedBox(height: 36),

              // Bouncing Dots
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(3, (index) {
                  return FadeTransition(
                    opacity: _dotControllers[index],
                    child: Container(
                      margin: const EdgeInsets.symmetric(horizontal: 4),
                      width: 12,
                      height: 12,
                      decoration: const BoxDecoration(
                        shape: BoxShape.circle,
                        color: AppColors.primary,
                      ),
                    ),
                  );
                }),
              ),
              const SizedBox(height: 24),

              const Text(
                'Processing payment...',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
              ),
              const SizedBox(height: 8),
              const Text(
                'AUREV AI is securely\nverifying your payment.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 14, color: AppColors.textSecondary, height: 1.4),
              ),

              const Spacer(),

              // Protected Footer
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: const [
                  Icon(Icons.lock_rounded, size: 14, color: AppColors.textLight),
                  SizedBox(width: 6),
                  Text('Protected by AUREV AI', style: TextStyle(fontSize: 12, color: AppColors.textLight)),
                ],
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }
}
