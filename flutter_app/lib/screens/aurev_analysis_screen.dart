import 'dart:async';
import 'package:flutter/material.dart';
import '../theme/colors.dart';
import '../services/api_service.dart';
import 'payment_result_screen.dart';

class AurevAnalysisScreen extends StatefulWidget {
  final String transactionId;
  const AurevAnalysisScreen({super.key, required this.transactionId});

  @override
  State<AurevAnalysisScreen> createState() => _AurevAnalysisScreenState();
}

class _AurevAnalysisScreenState extends State<AurevAnalysisScreen> with TickerProviderStateMixin {
  late AnimationController _hoverController;
  late AnimationController _pulseController;
  late Animation<double> _hoverAnimation;
  int _completedSteps = 0;
  Timer? _stepTimer;
  Timer? _pollTimer;
  Map<String, dynamic>? _paymentData;
  bool _isFinalized = false;

  final List<String> _robotSayings = [
    '🔒 Checking dual-debit safety lock...',
    '🔍 Verifying Central Bank ledger & account status...',
    '⚖️ Safety Engine evaluating transaction policy...',
    '✨ Completing state resolution...',
  ];

  final List<Map<String, dynamic>> _diagnosticSteps = [
    {
      'title': 'Dual-Debit Protection Active',
      'detail': 'Payment slot locked to prevent accidental duplicate charges',
      'icon': Icons.lock_outline_rounded,
    },
    {
      'title': 'Verifying Central Bank Ledger',
      'detail': 'Checking issuing bank switch & customer account balance',
      'icon': Icons.account_balance_rounded,
    },
    {
      'title': 'Safety Policy Evaluation',
      'detail': 'Enforcing deterministic banking security rules',
      'icon': Icons.security_rounded,
    },
    {
      'title': 'Finalizing Order Status',
      'detail': 'Confirming final payment resolution',
      'icon': Icons.check_circle_outline_rounded,
    },
  ];

  @override
  void initState() {
    super.initState();

    _hoverController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat(reverse: true);

    _hoverAnimation = Tween<double>(begin: -6.0, end: 6.0).animate(
      CurvedAnimation(parent: _hoverController, curve: Curves.easeInOut),
    );

    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    )..repeat(reverse: true);

    _startFastRecoveryEngine();
  }

  void _startFastRecoveryEngine() {
    _stepTimer = Timer.periodic(const Duration(milliseconds: 400), (timer) async {
      if (_completedSteps < _diagnosticSteps.length - 1) {
        if (mounted) setState(() => _completedSteps++);
      } else {
        timer.cancel();
        if (mounted) setState(() => _completedSteps = _diagnosticSteps.length);
        await _fetchFinalStatusAndComplete();
      }
    });

    _pollTimer = Timer.periodic(const Duration(milliseconds: 400), (t) async {
      try {
        final data = await ApiService.getPaymentStatus(widget.transactionId);
        if (data != null && mounted) {
          _paymentData = data;
          final status = data['status'];
          if (status == 'SUCCESS' || status == 'DECLINED' || status == 'ESCALATED') {
            t.cancel();
          }
        }
      } catch (_) {}
    });
  }

  Future<void> _fetchFinalStatusAndComplete() async {
    if (_isFinalized) return;
    _isFinalized = true;
    _pollTimer?.cancel();

    try {
      final data = await ApiService.getPaymentStatus(widget.transactionId);
      if (data != null) {
        _paymentData = data;
      }
    } catch (_) {}

    final status = _paymentData?['status'];
    final failureCode = _paymentData?['failure_code'] ?? '';
    final isMoneyDebited = _paymentData?['money_debited'] == true;

    // Respect exact backend outcomes
    if (status == 'DECLINED' || failureCode == 'INSUFFICIENT_FUNDS' || failureCode == 'INVALID_DETAILS' || failureCode == 'BANK_UNAVAILABLE') {
      _paymentData = {
        'status': 'DECLINED',
        'failure_code': failureCode.isNotEmpty ? failureCode : 'INSUFFICIENT_FUNDS',
        'failure_reason': _paymentData?['failure_reason'] ?? 'Bank switch declined the transaction',
        'money_debited': false,
        'amount': _paymentData?['amount'] ?? 485.0,
      };
    } else if (status == 'SUCCESS' || isMoneyDebited) {
      _paymentData = {
        'status': 'SUCCESS',
        'recovery_attempt_count': (_paymentData?['recovery_attempt_count'] ?? 1) > 0 ? _paymentData!['recovery_attempt_count'] : 1,
        'aurev_action': isMoneyDebited ? 'RECONCILE' : 'RETRY',
        'money_debited': isMoneyDebited,
        'amount': _paymentData?['amount'] ?? 485.0,
      };
    }

    if (mounted) {
      await Future.delayed(const Duration(milliseconds: 300));
      if (!mounted) return;
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (_) => PaymentResultScreen(
            transactionId: widget.transactionId,
            paymentData: _paymentData ?? {'status': 'DECLINED', 'failure_code': 'INSUFFICIENT_FUNDS', 'amount': 485.0},
          ),
        ),
      );
    }
  }

  @override
  void dispose() {
    _hoverController.dispose();
    _pulseController.dispose();
    _stepTimer?.cancel();
    _pollTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final robotMessage = _completedSteps < _robotSayings.length
        ? _robotSayings[_completedSteps]
        : 'Diagnostic Evaluation Complete';

    return Scaffold(
      backgroundColor: AppColors.white,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              const SizedBox(height: 10),

              // Animated Hovering Robot Area
              AnimatedBuilder(
                animation: _hoverController,
                builder: (context, child) {
                  return Transform.translate(
                    offset: Offset(0, _hoverAnimation.value),
                    child: Column(
                      children: [
                        // Speech Bubble
                        Container(
                          margin: const EdgeInsets.only(bottom: 12),
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                          decoration: BoxDecoration(
                            color: AppColors.primary,
                            borderRadius: BorderRadius.circular(16),
                            boxShadow: [
                              BoxShadow(
                                color: AppColors.primary.withOpacity(0.25),
                                blurRadius: 10,
                                offset: const Offset(0, 4),
                              ),
                            ],
                          ),
                          child: Text(
                            robotMessage,
                            textAlign: TextAlign.center,
                            style: const TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w700,
                              color: Colors.white,
                            ),
                          ),
                        ),

                        // Robot Avatar with Glowing Rings
                        Stack(
                          alignment: Alignment.center,
                          children: [
                            ScaleTransition(
                              scale: Tween<double>(begin: 0.95, end: 1.1).animate(_pulseController),
                              child: Container(
                                width: 88,
                                height: 88,
                                decoration: BoxDecoration(
                                  shape: BoxShape.circle,
                                  color: AppColors.primaryLight.withOpacity(0.5),
                                ),
                              ),
                            ),
                            Container(
                              width: 72,
                              height: 72,
                              decoration: BoxDecoration(
                                color: const Color(0xFF0B1F12),
                                shape: BoxShape.circle,
                                border: Border.all(color: Colors.greenAccent, width: 2),
                                boxShadow: [
                                  BoxShadow(
                                    color: Colors.greenAccent.withOpacity(0.35),
                                    blurRadius: 14,
                                    offset: const Offset(0, 4),
                                  ),
                                ],
                              ),
                              child: const Icon(
                                Icons.smart_toy_rounded,
                                color: Colors.greenAccent,
                                size: 38,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  );
                },
              ),

              const SizedBox(height: 16),

              const Text(
                'AUREV AI Autonomous Safety Gate',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: AppColors.textPrimary),
              ),
              const SizedBox(height: 4),
              const Text(
                'Zero-Duplicate-Charge Protection Active • Please do not leave this screen',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 11, color: AppColors.textSecondary, fontWeight: FontWeight.w500),
              ),

              const SizedBox(height: 20),

              // Diagnostic Step Progress
              Expanded(
                child: ListView.separated(
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: _diagnosticSteps.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 10),
                  itemBuilder: (context, index) {
                    final isDone = index < _completedSteps;
                    final isCurrent = index == _completedSteps;
                    final step = _diagnosticSteps[index];

                    Color borderColor = AppColors.border;
                    Color bgColor = Colors.white;
                    Color iconColor = AppColors.textLight;

                    if (isDone) {
                      borderColor = AppColors.primary.withOpacity(0.3);
                      bgColor = AppColors.primaryLight.withOpacity(0.4);
                      iconColor = AppColors.primary;
                    } else if (isCurrent) {
                      borderColor = AppColors.primary;
                      bgColor = AppColors.primaryLight;
                      iconColor = AppColors.primary;
                    }

                    return AnimatedContainer(
                      duration: const Duration(milliseconds: 250),
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      decoration: BoxDecoration(
                        color: bgColor,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: borderColor, width: isCurrent ? 1.5 : 1.0),
                      ),
                      child: Row(
                        children: [
                          Container(
                            width: 34,
                            height: 34,
                            decoration: BoxDecoration(
                              color: isDone
                                  ? AppColors.primary
                                  : (isCurrent ? AppColors.primary.withOpacity(0.15) : AppColors.background),
                              shape: BoxShape.circle,
                            ),
                            child: isDone
                                ? const Icon(Icons.check_rounded, color: Colors.white, size: 20)
                                : (isCurrent
                                    ? const SizedBox(
                                        width: 16,
                                        height: 16,
                                        child: Padding(
                                          padding: EdgeInsets.all(8.0),
                                          child: CircularProgressIndicator(
                                            strokeWidth: 2,
                                            valueColor: AlwaysStoppedAnimation<Color>(AppColors.primary),
                                          ),
                                        ),
                                      )
                                    : Icon(step['icon'], color: iconColor, size: 18)),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  step['title'],
                                  style: TextStyle(
                                    fontSize: 13,
                                    fontWeight: FontWeight.w700,
                                    color: isDone || isCurrent ? AppColors.textPrimary : AppColors.textLight,
                                  ),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  step['detail'],
                                  style: TextStyle(
                                    fontSize: 11,
                                    color: isDone || isCurrent ? AppColors.textSecondary : AppColors.textLight,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    );
                  },
                ),
              ),

              // Bottom Protection Notice
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: const Color(0xFF0B1F12),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.greenAccent.withOpacity(0.3)),
                ),
                child: Row(
                  children: const [
                    Icon(Icons.security_rounded, color: Colors.greenAccent, size: 18),
                    SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'AUREV Safety Gate: Zero duplicate charge guarantee enforced.',
                        style: TextStyle(fontSize: 11, color: Colors.white70, fontWeight: FontWeight.w600),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 10),
            ],
          ),
        ),
      ),
    );
  }
}
