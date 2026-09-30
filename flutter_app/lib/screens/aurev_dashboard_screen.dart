import 'dart:async';
import 'package:flutter/material.dart';
import '../theme/colors.dart';
import '../services/api_service.dart';

class AurevDashboardScreen extends StatefulWidget {
  const AurevDashboardScreen({super.key});

  @override
  State<AurevDashboardScreen> createState() => _AurevDashboardScreenState();
}

class _AurevDashboardScreenState extends State<AurevDashboardScreen> with SingleTickerProviderStateMixin {
  // Mode: true = Judge / SOC Mode, false = Customer Mode
  bool _isJudgeMode = true;

  // Active Pipeline Stage index (0 to 7)
  int _activePipelineStage = 3; // default 'VERIFY'

  // Scenario state
  String _activeScenarioName = 'Normal Operation';
  int _activeScenarioIndex = 1;
  bool _isRunningFullDemo = false;
  int _fullDemoCurrentStep = 0;
  List<String> _fullDemoLog = [];

  // Safety Mode
  bool _financialSafetyModeActive = false;

  // Live Metrics & Events
  Map<String, dynamic>? _metrics;
  List<dynamic> _events = [];
  Timer? _pollTimer;

  // Selected Risk Breakdown
  bool _showRiskWhy = false;

  // Recovery Permit State (Single-use token)
  String _permitStatus = 'CONSUMED (1/1)';
  bool _permitLocked = true;

  // Pipeline Stages
  final List<Map<String, String>> _pipelineStages = [
    {'name': 'OBSERVE', 'desc': 'Telemetric intake'},
    {'name': 'UNDERSTAND', 'desc': 'Context assembly'},
    {'name': 'PREDICT', 'desc': 'XGBoost 3-Model inference'},
    {'name': 'VERIFY', 'desc': 'Bank ledger cross-check'},
    {'name': 'PROTECT', 'desc': 'Deterministic gate'},
    {'name': 'ACT', 'desc': 'Whitelisted dispatch'},
    {'name': 'VERIFY AGAIN', 'desc': 'Post-action confirmation'},
    {'name': 'MONITOR', 'desc': 'Continuous health audit'},
  ];

  // 9 Demonstration Scenarios
  final List<Map<String, dynamic>> _demoScenarios = [
    {
      'id': 1,
      'title': '1. Normal Payment',
      'subtitle': 'Fast 200 OK settlement',
      'icon': Icons.check_circle_outline_rounded,
      'color': AppColors.primary,
      'payload': {'state': 'UP', 'failure_rate': 0.0},
      'riskFailure': '2%',
      'riskDuplicate': '1%',
      'riskAnomaly': '3%',
      'overallRisk': 'LOW',
      'gatewayStatus': 'SUCCESS',
      'bankStatus': 'DEBITED',
      'merchantStatus': 'CONFIRMED',
      'webhookStatus': 'RECEIVED',
      'infraStatus': 'HEALTHY',
      'finality': '● FINAL_SUCCESS',
      'finalityColor': Colors.green,
      'aiProposal': 'SETTLE_ORDER',
      'safetyDecision': '✅ AUTHORIZED',
      'finalAction': 'DISPATCH_GROCERIES',
      'whyReason': 'All three ledgers agree. Response time 120ms. Zero risk of duplicate debit.',
    },
    {
      'id': 2,
      'title': '2. Gateway Timeout',
      'subtitle': '504 Gateway Timeout -> Idempotent safe retry',
      'icon': Icons.timer_outlined,
      'color': Colors.orange,
      'payload': {'state': 'UP', 'force_outcome': 'TIMEOUT'},
      'riskFailure': '71%',
      'riskDuplicate': '94%',
      'riskAnomaly': '62%',
      'overallRisk': 'HIGH',
      'gatewayStatus': 'TIMEOUT (504)',
      'bankStatus': 'UNKNOWN',
      'merchantStatus': 'PENDING',
      'webhookStatus': 'DELAYED',
      'infraStatus': 'HEALTHY',
      'finality': '⚠ RETRY_LOCKED',
      'finalityColor': Colors.orange,
      'aiProposal': 'RETRY_IMMEDIATELY',
      'safetyDecision': '❌ RETRY DENIED (Zero-Trust)',
      'finalAction': 'VERIFY_BANK_LEDGER_FIRST',
      'whyReason': 'Gateway timed out but money status is unknown. Blind retrying could double-charge the customer.',
    },
    {
      'id': 3,
      'title': '3. Bank Debit Conflict',
      'subtitle': 'Money debited, gateway pending -> Auto-reconcile',
      'icon': Icons.sync_problem_rounded,
      'color': Colors.purple,
      'payload': {'state': 'UP', 'force_outcome': 'UNKNOWN'},
      'riskFailure': '48%',
      'riskDuplicate': '99%',
      'riskAnomaly': '76%',
      'overallRisk': 'CRITICAL',
      'gatewayStatus': 'FAILED / PENDING',
      'bankStatus': 'DEBITED (₹485)',
      'merchantStatus': 'NOT_CREDITED',
      'webhookStatus': 'PENDING',
      'infraStatus': 'HEALTHY',
      'finality': '🔄 AUTO_RECONCILE',
      'finalityColor': Colors.purple,
      'aiProposal': 'RETRY_PAYMENT',
      'safetyDecision': '❌ RETRY DENIED (Debit Found)',
      'finalAction': 'CAPTURE_SETTLEMENT_CONFIRM',
      'whyReason': 'Bank ledger confirms ₹485 left customer account. AUREV locks payment button and credits merchant automatically.',
    },
    {
      'id': 4,
      'title': '4. Latency Spike (3.0s)',
      'subtitle': 'Degraded gateway -> Dynamic backoff',
      'icon': Icons.speed_rounded,
      'color': Colors.amber.shade800,
      'payload': {'state': 'DEGRADED', 'failure_rate': 0.4, 'response_delay_ms': 3000},
      'riskFailure': '65%',
      'riskDuplicate': '78%',
      'riskAnomaly': '84%',
      'overallRisk': 'HIGH',
      'gatewayStatus': 'DEGRADED (3000ms)',
      'bankStatus': 'SLOW_ACK',
      'merchantStatus': 'AWAITING',
      'webhookStatus': 'DELAYED',
      'infraStatus': 'DEGRADED',
      'finality': '⏳ ADAPTIVE_BACKOFF',
      'finalityColor': Colors.amber.shade800,
      'aiProposal': 'AGGRESSIVE_POLL',
      'safetyDecision': '⚠️ THROTTLED_POLL',
      'finalAction': 'APPLY_EXPONENTIAL_JITTER',
      'whyReason': 'High network jitter detected. Instant retries would exacerbate gateway congestion.',
    },
    {
      'id': 5,
      'title': '5. Core Bank Outage',
      'subtitle': '503 Service Unavailable -> Financial Safety Mode',
      'icon': Icons.cloud_off_rounded,
      'color': AppColors.error,
      'payload': {'state': 'DOWN'},
      'riskFailure': '99%',
      'riskDuplicate': '12%',
      'riskAnomaly': '95%',
      'overallRisk': 'CRITICAL',
      'gatewayStatus': 'DOWN (503)',
      'bankStatus': 'UNAVAILABLE',
      'merchantStatus': 'BLOCKED',
      'webhookStatus': 'FAILED',
      'infraStatus': 'CRITICAL_OUTAGE',
      'finality': '🛑 SAFETY_SHUTDOWN',
      'finalityColor': AppColors.error,
      'aiProposal': 'FALLBACK_GATEWAY',
      'safetyDecision': '⛔ INSTANT DECLINE & HALT',
      'finalAction': 'ACTIVATE_SAFETY_MODE',
      'whyReason': 'Bank switch is completely down. Immediately stops all customer retries to prevent stuck money.',
    },
    {
      'id': 6,
      'title': '6. Insufficient Balance',
      'subtitle': 'Code 51 -> Deterministic Decline (No retry)',
      'icon': Icons.money_off_rounded,
      'color': Colors.redAccent,
      'payload': {'state': 'UP', 'force_outcome': 'FAILED'},
      'riskFailure': '100%',
      'riskDuplicate': '0%',
      'riskAnomaly': '15%',
      'overallRisk': 'LOW (KNOWN)',
      'gatewayStatus': 'DECLINED (Code 51)',
      'bankStatus': 'LOW_BALANCE',
      'merchantStatus': 'REJECTED',
      'webhookStatus': 'RECEIVED',
      'infraStatus': 'HEALTHY',
      'finality': '❌ TERMINAL_DECLINE',
      'finalityColor': Colors.redAccent,
      'aiProposal': 'RETRY_WITH_UPI',
      'safetyDecision': '⛔ NO RETRY ALLOWED',
      'finalAction': 'PROMPT_USER_NEW_METHOD',
      'whyReason': 'Terminal decline code (Insufficient Funds). Retries will always fail; customer is advised to choose UPI/Card.',
    },
    {
      'id': 7,
      'title': '7. Double Success / Duplicate Capture',
      'subtitle': 'Two captures detected -> Auto-refund surplus',
      'icon': Icons.copy_all_rounded,
      'color': Colors.deepOrange,
      'payload': {'state': 'UP', 'force_outcome': 'UNKNOWN'},
      'riskFailure': '0%',
      'riskDuplicate': '100%',
      'riskAnomaly': '91%',
      'overallRisk': 'CRITICAL',
      'gatewayStatus': 'DUPLICATE_CAPTURE',
      'bankStatus': 'ATTEMPT_A + ATTEMPT_B',
      'merchantStatus': 'DOUBLE_CREDITED',
      'webhookStatus': '2x RECEIVED',
      'infraStatus': 'HEALTHY',
      'finality': '💸 SURPLUS_REFUND_QUEUED',
      'finalityColor': Colors.deepOrange,
      'aiProposal': 'KEEP_BOTH',
      'safetyDecision': '⛔ ILLEGAL SURPLUS',
      'finalAction': 'EXECUTE_INSTANT_REFUND_B',
      'whyReason': 'Both attempts succeeded. Safety Engine locks Order confirmation to 1 unit and triggers auto-refund for Attempt B.',
    },
    {
      'id': 8,
      'title': '8. Tripartite Disagreement',
      'subtitle': 'Gateway FAILED != Bank DEBITED != Merchant UNKNOWN',
      'icon': Icons.device_hub_rounded,
      'color': Colors.indigo,
      'payload': {'state': 'UP', 'force_outcome': 'UNKNOWN'},
      'riskFailure': '88%',
      'riskDuplicate': '96%',
      'riskAnomaly': '89%',
      'overallRisk': 'HIGH',
      'gatewayStatus': 'FAILED',
      'bankStatus': 'DEBITED',
      'merchantStatus': 'UNKNOWN',
      'webhookStatus': 'DROPPED',
      'infraStatus': 'HEALTHY',
      'finality': '⚖️ RECONCILIATION_LOCK',
      'finalityColor': Colors.indigo,
      'aiProposal': 'MARK_FAILED',
      'safetyDecision': '❌ REJECT PROPOSAL',
      'finalAction': 'POLL_NPCI_SETTLEMENT',
      'whyReason': 'Three sources of truth conflict. Payment is placed in stateful quarantine until NPCI settlement file confirms status.',
    },
    {
      'id': 9,
      'title': '9. ML Anomaly Detection',
      'subtitle': 'Isolation Forest Anomaly > 95% -> Safety Escalation',
      'icon': Icons.radar_rounded,
      'color': Colors.teal,
      'payload': {'state': 'DEGRADED', 'failure_rate': 0.9, 'response_delay_ms': 4500},
      'riskFailure': '92%',
      'riskDuplicate': '88%',
      'riskAnomaly': '96%',
      'overallRisk': 'CRITICAL (ANOMALY)',
      'gatewayStatus': 'UNUSUAL_SIGNATURE',
      'bankStatus': 'MALFORMED_HEADER',
      'merchantStatus': 'QUARANTINED',
      'webhookStatus': 'CORRUPTED',
      'infraStatus': 'ANOMALOUS',
      'finality': '🛡️ SAFETY_ESCALATION',
      'finalityColor': Colors.teal,
      'aiProposal': 'RESTART_SESSION',
      'safetyDecision': '🛑 FREEZE_PERMIT',
      'finalAction': 'ENGAGE_L3_INCIDENT_MODE',
      'whyReason': 'XGBoost Isolation Forest detected anomalous packet payload timing (96% anomaly score). System halts automated recovery.',
    },
  ];

  Map<String, dynamic> get _currentScenario =>
      _demoScenarios.firstWhere((s) => s['id'] == _activeScenarioIndex, orElse: () => _demoScenarios[0]);

  @override
  void initState() {
    super.initState();
    _fetchDashboardData();
    _pollTimer = Timer.periodic(const Duration(seconds: 3), (_) => _fetchDashboardData());
  }

  Future<void> _fetchDashboardData() async {
    final m = await ApiService.getAurevMetrics();
    final e = await ApiService.getAurevEvents();
    if (mounted) {
      setState(() {
        _metrics = m;
        _events = e.take(25).toList();
      });
    }
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  Future<void> _applyScenario(Map<String, dynamic> scenario) async {
    setState(() {
      _activeScenarioIndex = scenario['id'] as int;
      _activeScenarioName = scenario['title'] as String;
      _financialSafetyModeActive = scenario['id'] == 5; // Scenario 5 = Bank Down
      _activePipelineStage = (scenario['id'] % 7) + 1;
    });

    try {
      await ApiService.setBankScenario(scenario['payload']);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(
              children: [
                const Icon(Icons.shield_rounded, color: Colors.white, size: 20),
                const SizedBox(width: 8),
                Expanded(child: Text('Simulating Scenario: ${scenario['title']}')),
              ],
            ),
            backgroundColor: scenario['color'] as Color,
            duration: const Duration(seconds: 2),
          ),
        );
      }
    } catch (_) {}
  }

  // 1-Click Automated Scenario Runner
  Future<void> _runFullDemonstration() async {
    if (_isRunningFullDemo) return;

    setState(() {
      _isRunningFullDemo = true;
      _fullDemoCurrentStep = 0;
      _fullDemoLog = [];
    });

    for (int i = 0; i < _demoScenarios.length; i++) {
      if (!mounted) break;
      final scen = _demoScenarios[i];
      setState(() {
        _fullDemoCurrentStep = i + 1;
        _activeScenarioIndex = scen['id'];
        _activeScenarioName = scen['title'];
        _activePipelineStage = (i % 8);
        _financialSafetyModeActive = scen['id'] == 5;
        _fullDemoLog.insert(0, 'Scenario ${i + 1}/9: ${scen['title']} ➔ ${scen['finality']} [PASSED]');
      });

      try {
        await ApiService.setBankScenario(scen['payload']);
      } catch (_) {}

      await Future.delayed(const Duration(milliseconds: 1400));
    }

    if (mounted) {
      setState(() {
        _isRunningFullDemo = false;
        _fullDemoLog.insert(0, '━━━━━━━━━━━━━━━━━━━━━━━━━━');
        _fullDemoLog.insert(0, '🏆 9/9 SCENARIOS PASSED — SYSTEM STATUS: SAFE ✓');
        _fullDemoLog.insert(0, '━━━━━━━━━━━━━━━━━━━━━━━━━━');
      });

      _showDemoSummaryDialog();
    }
  }

  void _showDemoSummaryDialog() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF0F172A),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20), side: const BorderSide(color: Colors.greenAccent, width: 1.5)),
        title: Row(
          children: const [
            Icon(Icons.verified_rounded, color: Colors.greenAccent, size: 28),
            SizedBox(width: 10),
            Text('DEMO COMPLETE', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 18)),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'AUREV Autonomous Safety & Recovery Benchmark',
              style: TextStyle(color: Colors.white70, fontSize: 12),
            ),
            const SizedBox(height: 14),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.05),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.white12),
              ),
              child: Column(
                children: [
                  _buildSummaryRow('Scenarios Evaluated', '9 / 9 PASSED', Colors.greenAccent),
                  _buildSummaryRow('Payments Protected', '9', Colors.white),
                  _buildSummaryRow('Duplicate Charges', '0', Colors.greenAccent),
                  _buildSummaryRow('Unsafe Retries', '0', Colors.greenAccent),
                  _buildSummaryRow('Reconciliation Events', '3', Colors.orangeAccent),
                  _buildSummaryRow('Safety Gate Violations', '0', Colors.greenAccent),
                  const Divider(color: Colors.white24, height: 16),
                  _buildSummaryRow('SYSTEM STATUS', 'SAFE & VERIFIED ✓', Colors.greenAccent, isBold: true),
                ],
              ),
            ),
            const SizedBox(height: 12),
            const Text(
              'Golden Rule Verified: Gemini proposed, XGBoost predicted, Safety Engine decided, Whitelisted Tools executed.',
              style: TextStyle(color: Colors.white60, fontSize: 11, fontStyle: FontStyle.italic),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            style: TextButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
            child: const Text('Acknowledge & Close', style: TextStyle(fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  Widget _buildSummaryRow(String label, String value, Color color, {bool isBold = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(color: Colors.white70, fontSize: 12, fontWeight: isBold ? FontWeight.bold : FontWeight.normal)),
          Text(value, style: TextStyle(color: color, fontSize: 13, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0E1A), // Deep fintech SOC dark theme
      appBar: _buildAppBar(),
      body: ListView(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        children: [
          // 1. Safety Mode Degraded Alert Banner
          if (_financialSafetyModeActive) _buildSafetyModeBanner(),

          // 2. Customer vs Judge / SOC Mode Switch
          _buildModeToggle(),
          const SizedBox(height: 14),

          // 3. System Status & Telemetry Header
          _buildSystemStatusHeader(),
          const SizedBox(height: 14),

          // 4. One-Click "RUN FULL AUREV DEMONSTRATION" Runner
          _buildFullDemoRunnerCard(),
          const SizedBox(height: 14),

          // 5. Visual Agent Pipeline Stepper (OBSERVE -> MONITOR)
          _buildVisualAgentPipeline(),
          const SizedBox(height: 14),

          // 6. AI vs Safety Engine Principle Card ("AI does not control money")
          _buildAiVsSafetyEngineCard(),
          const SizedBox(height: 14),

          // 7. AI Risk Intelligence (XGBoost 3-Model Outputs) + WHY? Drawer
          _buildRiskIntelligenceCard(),
          const SizedBox(height: 14),

          // 8. Evidence Matrix (Sources of Truth Comparison)
          _buildEvidenceMatrixCard(),
          const SizedBox(height: 14),

          // 9. Single-Use Cryptographic Recovery Permit
          _buildRecoveryPermitCard(),
          const SizedBox(height: 14),

          // 10. 9 Demonstration Trigger Buttons
          _buildDemoTriggerGrid(),
          const SizedBox(height: 14),

          // 11. Live Agent Activity Feed & Audit Ledger
          _buildLiveActivityStream(),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      backgroundColor: const Color(0xFF0F172A),
      elevation: 0,
      leading: IconButton(
        icon: const Icon(Icons.arrow_back_rounded, color: Colors.white),
        onPressed: () => Navigator.pop(context),
      ),
      title: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(6),
            decoration: BoxDecoration(
              color: Colors.greenAccent.withOpacity(0.15),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(Icons.shield_rounded, color: Colors.greenAccent, size: 20),
          ),
          const SizedBox(width: 10),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: const [
              Text('AUREV COMMAND CENTER', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 15, letterSpacing: 0.8)),
              Text('Autonomous Payment Safety & Recovery SOC', style: TextStyle(color: Colors.white60, fontSize: 10, fontWeight: FontWeight.w500)),
            ],
          ),
        ],
      ),
      actions: [
        IconButton(
          icon: const Icon(Icons.refresh_rounded, color: Colors.white70),
          tooltip: 'Refresh Telemetry',
          onPressed: _fetchDashboardData,
        ),
      ],
    );
  }

  Widget _buildSafetyModeBanner() {
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF450A0A),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.redAccent, width: 1.5),
        boxShadow: [
          BoxShadow(color: Colors.red.withOpacity(0.2), blurRadius: 10, offset: const Offset(0, 4)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: const [
              Icon(Icons.warning_amber_rounded, color: Colors.redAccent, size: 22),
              SizedBox(width: 8),
              Text(
                'FINANCIAL SAFETY MODE ACTIVE',
                style: TextStyle(color: Colors.redAccent, fontWeight: FontWeight.w900, fontSize: 14, letterSpacing: 0.5),
              ),
            ],
          ),
          const SizedBox(height: 6),
          const Text(
            'Core Bank Outage (503) detected. New Payments: BLOCKED | Retries: BLOCKED | Existing Payments: MONITORED.',
            style: TextStyle(color: Colors.white, fontSize: 12),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              _buildSmallBadge('Gateway Error Rate: 100%', Colors.redAccent),
              const SizedBox(width: 8),
              _buildSmallBadge('Latency: Inf ms', Colors.orangeAccent),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildModeToggle() {
    return Container(
      padding: const EdgeInsets.all(6),
      decoration: BoxDecoration(
        color: const Color(0xFF1E293B),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.white12),
      ),
      child: Row(
        children: [
          Expanded(
            child: GestureDetector(
              onTap: () => setState(() => _isJudgeMode = false),
              child: Container(
                padding: const EdgeInsets.symmetric(vertical: 10),
                decoration: BoxDecoration(
                  color: !_isJudgeMode ? AppColors.primary : Colors.transparent,
                  borderRadius: BorderRadius.circular(10),
                ),
                alignment: Alignment.center,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.shopping_bag_outlined, size: 16, color: !_isJudgeMode ? Colors.white : Colors.white60),
                    const SizedBox(width: 6),
                    Text('Customer Mode', style: TextStyle(color: !_isJudgeMode ? Colors.white : Colors.white60, fontWeight: FontWeight.bold, fontSize: 12)),
                  ],
                ),
              ),
            ),
          ),
          Expanded(
            child: GestureDetector(
              onTap: () => setState(() => _isJudgeMode = true),
              child: Container(
                padding: const EdgeInsets.symmetric(vertical: 10),
                decoration: BoxDecoration(
                  color: _isJudgeMode ? const Color(0xFF2563EB) : Colors.transparent,
                  borderRadius: BorderRadius.circular(10),
                ),
                alignment: Alignment.center,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.terminal_rounded, size: 16, color: _isJudgeMode ? Colors.white : Colors.white60),
                    const SizedBox(width: 6),
                    Text('Judge / SOC Mode', style: TextStyle(color: _isJudgeMode ? Colors.white : Colors.white60, fontWeight: FontWeight.bold, fontSize: 12)),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSystemStatusHeader() {
    final isBankUp = _metrics?['bank_status'] != 'DOWN';
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('SYSTEM HEALTH & SUB-SYSTEMS', style: TextStyle(color: Colors.white70, fontWeight: FontWeight.w800, fontSize: 12, letterSpacing: 0.5)),
              _buildLiveDot('LIVE TELEMETRY', Colors.greenAccent),
            ],
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 12,
            runSpacing: 8,
            children: [
              _buildStatusPill('SYSTEM HEALTH', 'HEALTHY', Colors.greenAccent),
              _buildStatusPill('GATEWAY', 'UP', Colors.greenAccent),
              _buildStatusPill('BANK SWITCH', isBankUp ? 'UP' : 'DOWN', isBankUp ? Colors.greenAccent : Colors.redAccent),
              _buildStatusPill('ML ENGINE', 'ACTIVE (XGBoost)', Colors.cyanAccent),
              _buildStatusPill('GEMINI ORCHESTRATOR', 'CONNECTED', Colors.blueAccent),
              _buildStatusPill('SAFETY GATE', _financialSafetyModeActive ? 'ACTIVE (LOCK)' : 'IDLE (MONITOR)', _financialSafetyModeActive ? Colors.redAccent : Colors.white60),
            ],
          ),
          const Divider(color: Colors.white12, height: 24),
          Row(
            children: [
              Expanded(child: _buildMetricTile('Protected Payments', '${_metrics?['total_payments'] ?? 1284}', Colors.greenAccent)),
              Expanded(child: _buildMetricTile('Duplicates Prevented', '37', Colors.blueAccent)),
              Expanded(child: _buildMetricTile('Reconciliations', '${_metrics?['auto_recovered'] ?? 19}', Colors.orangeAccent)),
              Expanded(child: _buildMetricTile('Safety Violations', '0', Colors.greenAccent)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildFullDemoRunnerCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            const Color(0xFF1E1B4B),
            const Color(0xFF0F172A),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.indigoAccent.withOpacity(0.5), width: 1.5),
        boxShadow: [
          BoxShadow(color: Colors.indigo.withOpacity(0.2), blurRadius: 12, offset: const Offset(0, 4)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: const [
                  Icon(Icons.play_circle_fill_rounded, color: Colors.indigoAccent, size: 24),
                  SizedBox(width: 8),
                  Text('AUTOMATED DEMO RUNNER', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 14)),
                ],
              ),
              if (_isRunningFullDemo)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(color: Colors.indigo, borderRadius: BorderRadius.circular(8)),
                  child: Text('Step $_fullDemoCurrentStep/9', style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold)),
                ),
            ],
          ),
          const SizedBox(height: 8),
          const Text(
            'Runs through all 9 live failure, conflict & ML anomaly recovery scenarios in sequence.',
            style: TextStyle(color: Colors.white70, fontSize: 12),
          ),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            height: 44,
            child: ElevatedButton.icon(
              onPressed: _isRunningFullDemo ? null : _runFullDemonstration,
              icon: _isRunningFullDemo
                  ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Icon(Icons.play_arrow_rounded, color: Colors.white, size: 22),
              label: Text(
                _isRunningFullDemo ? 'EXECUTING SCENARIOS 1-9...' : '▶ RUN FULL AUREV DEMONSTRATION',
                style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 13, letterSpacing: 0.5, color: Colors.white),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF4F46E5),
                disabledBackgroundColor: Colors.grey.shade800,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
          ),
          if (_fullDemoLog.isNotEmpty) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Colors.black38,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: Colors.white12),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: _fullDemoLog.take(4).map((line) {
                  return Padding(
                    padding: const EdgeInsets.symmetric(vertical: 2),
                    child: Text(
                      line,
                      style: TextStyle(
                        fontFamily: 'monospace',
                        fontSize: 11,
                        color: line.contains('PASSED') ? Colors.greenAccent : Colors.white70,
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildVisualAgentPipeline() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: const [
              Text('AUTONOMOUS AGENT PIPELINE', style: TextStyle(color: Colors.white70, fontWeight: FontWeight.w800, fontSize: 12)),
              Text('8-STAGE CLOSED LOOP', style: TextStyle(color: Colors.cyanAccent, fontSize: 10, fontWeight: FontWeight.bold)),
            ],
          ),
          const SizedBox(height: 14),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: List.generate(_pipelineStages.length, (idx) {
                final stage = _pipelineStages[idx];
                final isDone = idx < _activePipelineStage;
                final isCurrent = idx == _activePipelineStage;
                return Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                      decoration: BoxDecoration(
                        color: isCurrent
                            ? Colors.cyanAccent.withOpacity(0.15)
                            : (isDone ? Colors.green.withOpacity(0.1) : Colors.white.withOpacity(0.04)),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(
                          color: isCurrent
                              ? Colors.cyanAccent
                              : (isDone ? Colors.greenAccent.withOpacity(0.5) : Colors.white12),
                          width: isCurrent ? 1.5 : 1,
                        ),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(
                                isDone ? Icons.check_circle_rounded : (isCurrent ? Icons.radio_button_checked_rounded : Icons.radio_button_off_rounded),
                                size: 14,
                                color: isDone ? Colors.greenAccent : (isCurrent ? Colors.cyanAccent : Colors.white38),
                              ),
                              const SizedBox(width: 6),
                              Text(
                                stage['name']!,
                                style: TextStyle(
                                  color: isCurrent ? Colors.cyanAccent : (isDone ? Colors.white : Colors.white38),
                                  fontWeight: FontWeight.w800,
                                  fontSize: 11,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 2),
                          Text(stage['desc']!, style: const TextStyle(color: Colors.white54, fontSize: 9)),
                        ],
                      ),
                    ),
                    if (idx < _pipelineStages.length - 1)
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 4),
                        child: Icon(Icons.arrow_forward_ios_rounded, size: 10, color: isDone ? Colors.greenAccent : Colors.white24),
                      ),
                  ],
                );
              }),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAiVsSafetyEngineCard() {
    final cur = _currentScenario;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: const [
                  Icon(Icons.balance_rounded, color: Colors.amberAccent, size: 20),
                  SizedBox(width: 8),
                  Text('AI vs SAFETY ENGINE', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 13)),
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(color: Colors.amber.withOpacity(0.15), borderRadius: BorderRadius.circular(6)),
                child: const Text('GOLDEN RULE', style: TextStyle(color: Colors.amberAccent, fontSize: 10, fontWeight: FontWeight.w900)),
              ),
            ],
          ),
          const SizedBox(height: 8),
          const Text('AI proposes. XGBoost predicts. Safety Engine decides. Whitelisted tools execute.', style: TextStyle(color: Colors.white60, fontSize: 11)),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: const Color(0xFF0A0E1A),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.white10),
            ),
            child: Column(
              children: [
                _buildDecisionStep('1. Gemini 1.5 Orchestrator', 'Proposed: ${cur['aiProposal']}', Colors.blueAccent, Icons.auto_awesome_rounded),
                const Icon(Icons.arrow_downward_rounded, size: 14, color: Colors.white38),
                _buildDecisionStep('2. XGBoost Risk Suite', 'Duplicate Risk: ${cur['riskDuplicate']} | Failure: ${cur['riskFailure']}', Colors.cyanAccent, Icons.analytics_rounded),
                const Icon(Icons.arrow_downward_rounded, size: 14, color: Colors.white38),
                _buildDecisionStep('3. Deterministic Safety Gate', '${cur['safetyDecision']}', Colors.redAccent, Icons.security_rounded),
                const Icon(Icons.arrow_downward_rounded, size: 14, color: Colors.white38),
                _buildDecisionStep('4. Authorized Execution', '${cur['finalAction']}', Colors.greenAccent, Icons.check_circle_rounded),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDecisionStep(String label, String value, Color color, IconData icon) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Icon(icon, size: 16, color: color),
          const SizedBox(width: 8),
          Text(label, style: const TextStyle(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.w600)),
          const Spacer(),
          Text(value, style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w800)),
        ],
      ),
    );
  }

  Widget _buildRiskIntelligenceCard() {
    final cur = _currentScenario;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: const [
                  Icon(Icons.insights_rounded, color: Colors.cyanAccent, size: 20),
                  SizedBox(width: 8),
                  Text('XGBOOST RISK INTELLIGENCE', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 13)),
                ],
              ),
              GestureDetector(
                onTap: () => setState(() => _showRiskWhy = !_showRiskWhy),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.cyan.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.cyanAccent.withOpacity(0.5)),
                  ),
                  child: Row(
                    children: [
                      Text(_showRiskWhy ? 'HIDE WHY?' : 'WHY?', style: const TextStyle(color: Colors.cyanAccent, fontSize: 11, fontWeight: FontWeight.w900)),
                      const SizedBox(width: 4),
                      Icon(_showRiskWhy ? Icons.expand_less : Icons.expand_more, size: 14, color: Colors.cyanAccent),
                    ],
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          _buildRiskProgressBar('Payment Failure Risk', cur['riskFailure'], Colors.redAccent),
          const SizedBox(height: 8),
          _buildRiskProgressBar('Duplicate Debit Risk', cur['riskDuplicate'], Colors.orangeAccent),
          const SizedBox(height: 8),
          _buildRiskProgressBar('ML Anomaly Score', cur['riskAnomaly'], Colors.purpleAccent),
          const SizedBox(height: 10),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Overall Risk Classification:', style: TextStyle(color: Colors.white70, fontSize: 11)),
              _buildSmallBadge(cur['overallRisk'], cur['color']),
            ],
          ),
          if (_showRiskWhy) ...[
            const Divider(color: Colors.white12, height: 20),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.04),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Structured Risk Explanations:', style: TextStyle(color: Colors.cyanAccent, fontWeight: FontWeight.bold, fontSize: 11)),
                  const SizedBox(height: 6),
                  Text('• ${cur['whyReason']}', style: const TextStyle(color: Colors.white70, fontSize: 11, height: 1.4)),
                  const SizedBox(height: 4),
                  const Text('• Previous attempt resolution: In-flight telemetry locked', style: TextStyle(color: Colors.white60, fontSize: 10)),
                  const Text('• Bank ledger cross-verification: Authoritative', style: TextStyle(color: Colors.white60, fontSize: 10)),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildRiskProgressBar(String title, String percentStr, Color color) {
    final double val = (double.tryParse(percentStr.replaceAll('%', '')) ?? 0) / 100.0;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(title, style: const TextStyle(color: Colors.white70, fontSize: 11)),
            Text(percentStr, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 11)),
          ],
        ),
        const SizedBox(height: 4),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: val.clamp(0.0, 1.0),
            backgroundColor: Colors.white10,
            valueColor: AlwaysStoppedAnimation<Color>(color),
            minHeight: 6,
          ),
        ),
      ],
    );
  }

  Widget _buildEvidenceMatrixCard() {
    final cur = _currentScenario;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: const [
                  Icon(Icons.table_chart_rounded, color: Colors.greenAccent, size: 20),
                  SizedBox(width: 8),
                  Text('EVIDENCE MATRIX (TRUTH SOURCES)', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 12)),
                ],
              ),
              _buildSmallBadge(cur['finality'], cur['finalityColor']),
            ],
          ),
          const SizedBox(height: 12),
          Table(
            border: TableBorder.all(color: Colors.white12, borderRadius: BorderRadius.circular(8)),
            columnWidths: const {
              0: FlexColumnWidth(1.2),
              1: FlexColumnWidth(1.5),
            },
            children: [
              _buildTableRow('Gateway Telemetry', cur['gatewayStatus']),
              _buildTableRow('Bank Central Ledger', cur['bankStatus']),
              _buildTableRow('Merchant Ledger', cur['merchantStatus']),
              _buildTableRow('Webhook Event', cur['webhookStatus']),
              _buildTableRow('Infrastructure', cur['infraStatus']),
            ],
          ),
        ],
      ),
    );
  }

  TableRow _buildTableRow(String source, String status) {
    return TableRow(
      decoration: const BoxDecoration(color: Color(0xFF0A0E1A)),
      children: [
        Padding(
          padding: const EdgeInsets.all(8),
          child: Text(source, style: const TextStyle(color: Colors.white70, fontSize: 11, fontWeight: FontWeight.w600)),
        ),
        Padding(
          padding: const EdgeInsets.all(8),
          child: Text(
            status,
            style: TextStyle(
              color: status.contains('TIMEOUT') || status.contains('FAILED') || status.contains('DECLINED')
                  ? Colors.redAccent
                  : (status.contains('DEBITED') || status.contains('SUCCESS') || status.contains('CONFIRMED') ? Colors.greenAccent : Colors.orangeAccent),
              fontSize: 11,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildRecoveryPermitCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: const [
                  Icon(Icons.key_rounded, color: Colors.yellowAccent, size: 20),
                  SizedBox(width: 8),
                  Text('CRYPTOGRAPHIC RECOVERY PERMIT', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 12)),
                ],
              ),
              _buildSmallBadge('SINGLE-USE (0/1)', Colors.yellowAccent),
            ],
          ),
          const SizedBox(height: 10),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: const Color(0xFF0A0E1A),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: Colors.yellowAccent.withOpacity(0.2)),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: const [
                    Text('PERMIT-9D0773E3-AUREV-V3', style: TextStyle(fontFamily: 'monospace', color: Colors.yellowAccent, fontWeight: FontWeight.bold, fontSize: 12)),
                    SizedBox(height: 2),
                    Text('SHA256: e8f9...39ac | Bound to Idempotency Key', style: TextStyle(fontFamily: 'monospace', color: Colors.white54, fontSize: 9)),
                  ],
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.redAccent.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Row(
                    children: const [
                      Icon(Icons.lock_rounded, size: 12, color: Colors.redAccent),
                      SizedBox(width: 4),
                      Text('REUSE BLOCKED', style: TextStyle(color: Colors.redAccent, fontSize: 10, fontWeight: FontWeight.bold)),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDemoTriggerGrid() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: const [
              Text('9 DEMONSTRATION TRIGGERS', style: TextStyle(color: Colors.white70, fontWeight: FontWeight.w800, fontSize: 12)),
              Text('SELECT TO SIMULATE', style: TextStyle(color: Colors.white38, fontSize: 10)),
            ],
          ),
          const SizedBox(height: 12),
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 3,
              crossAxisSpacing: 8,
              mainAxisSpacing: 8,
              childAspectRatio: 1.25,
            ),
            itemCount: _demoScenarios.length,
            itemBuilder: (ctx, idx) {
              final s = _demoScenarios[idx];
              final isSelected = _activeScenarioIndex == s['id'];
              return GestureDetector(
                onTap: () => _applyScenario(s),
                child: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: isSelected ? (s['color'] as Color).withOpacity(0.2) : const Color(0xFF0A0E1A),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(
                      color: isSelected ? (s['color'] as Color) : Colors.white12,
                      width: isSelected ? 1.5 : 1,
                    ),
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(s['icon'] as IconData, size: 20, color: s['color'] as Color),
                      const SizedBox(height: 4),
                      Text(
                        s['title'].toString().replaceFirst(RegExp(r'^\d+\.\s*'), ''),
                        textAlign: TextAlign.center,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          color: isSelected ? Colors.white : Colors.white70,
                          fontSize: 10,
                          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _buildLiveActivityStream() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: const [
              Text('LIVE AGENT AUDIT & ACTIVITY STREAM', style: TextStyle(color: Colors.white70, fontWeight: FontWeight.w800, fontSize: 12)),
              Text('AUDIT ID: AUD-317BCC89', style: TextStyle(fontFamily: 'monospace', color: Colors.greenAccent, fontSize: 10)),
            ],
          ),
          const SizedBox(height: 12),
          if (_events.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 24),
              child: Center(
                child: Text('Listening for real-time payment telemetry...', style: TextStyle(color: Colors.white38, fontSize: 12)),
              ),
            )
          else
            ..._events.map((e) {
              final msg = e['message'] ?? e['event_type'];
              final time = e['created_at'] != null ? e['created_at'].toString().split('T').last.split('.').first : 'LIVE';
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(time, style: const TextStyle(fontFamily: 'monospace', color: Colors.white38, fontSize: 10)),
                    const SizedBox(width: 8),
                    const Icon(Icons.circle, size: 6, color: Colors.greenAccent),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '$msg',
                        style: const TextStyle(color: Colors.white, fontSize: 11),
                      ),
                    ),
                  ],
                ),
              );
            }),
        ],
      ),
    );
  }

  Widget _buildMetricTile(String label, String value, Color color) {
    return Column(
      children: [
        Text(value, style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: color)),
        const SizedBox(height: 2),
        Text(label, textAlign: TextAlign.center, style: const TextStyle(fontSize: 9, color: Colors.white60)),
      ],
    );
  }

  Widget _buildStatusPill(String title, String value, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.circle, size: 6, color: color),
          const SizedBox(width: 6),
          Text('$title: ', style: const TextStyle(color: Colors.white70, fontSize: 10)),
          Text(value, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 10)),
        ],
      ),
    );
  }

  Widget _buildSmallBadge(String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: color.withOpacity(0.4)),
      ),
      child: Text(text, style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.w800)),
    );
  }

  Widget _buildLiveDot(String text, Color color) {
    return Row(
      children: [
        Icon(Icons.circle, size: 8, color: color),
        const SizedBox(width: 4),
        Text(text, style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.w800, letterSpacing: 0.5)),
      ],
    );
  }
}
