"""
AUREV Controlled Tool Dispatcher & Safety Validation Gate.
Implements:
1. Strict schema validation for all Observation, Action, and Monitoring tools.
2. Safety Policy Engine authorization checks before executing any action tool.
3. Structured rejection (ACTION_DENIED) for unsafe tool calls.
4. Audit trail logging for every tool invocation.
"""
import inspect
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

from memory.event_timeline import timeline_store
from memory.payment_memory import payment_memory
from models.enums import BankStatus, EventType, FinalityState, GatewayStatus
from models.decisions import SystemHealthState
from safety.duplicate_protection import DuplicateProtection
from safety.finality_engine import FinalityEngine
from safety.recovery_permit import RecoveryPermitManager
from tools.action_tools import (
    allow_retry,
    block_pay_again,
    create_recovery_permit,
    create_support_case,
    notify_merchant,
    notify_user,
    request_payment_status,
    switch_gateway,
    trigger_eligible_refund,
    trigger_reconciliation,
)
from tools.monitoring_tools import (
    watch_gateway,
    watch_payment,
    watch_reconciliation,
    watch_server,
    watch_webhook,
)
from tools.observation_tools import (
    _system_health,
    get_attempt_history,
    get_customer_session,
    get_gateway_status,
    get_payment_state,
    get_reconciliation_status,
    get_risk_signals,
    get_server_health,
    get_transaction_status,
    get_webhook_status,
)

logger = logging.getLogger("aurev.tools.dispatcher")

OBSERVATION_TOOLS = {
    "get_payment_state": get_payment_state,
    "get_attempt_history": get_attempt_history,
    "get_gateway_status": get_gateway_status,
    "get_server_health": get_server_health,
    "get_webhook_status": get_webhook_status,
    "get_transaction_status": get_transaction_status,
    "get_customer_session": get_customer_session,
    "get_risk_signals": get_risk_signals,
    "get_reconciliation_status": get_reconciliation_status,
}

MONITORING_TOOLS = {
    "watch_payment": watch_payment,
    "watch_gateway": watch_gateway,
    "watch_server": watch_server,
    "watch_webhook": watch_webhook,
    "watch_reconciliation": watch_reconciliation,
}

ACTION_TOOLS = {
    "block_pay_again": block_pay_again,
    "allow_retry": allow_retry,
    "create_recovery_permit": create_recovery_permit,
    "request_payment_status": request_payment_status,
    "trigger_reconciliation": trigger_reconciliation,
    "switch_gateway": switch_gateway,
    "create_support_case": create_support_case,
    "trigger_eligible_refund": trigger_eligible_refund,
    "notify_user": notify_user,
    "notify_merchant": notify_merchant,
}

ALLOWED_TOOLS: Dict[str, Callable] = {
    **OBSERVATION_TOOLS,
    **MONITORING_TOOLS,
    **ACTION_TOOLS,
}

TOOL_SCHEMAS: List[Dict[str, Any]] = [
    # Observation Tools
    {
        "name": "get_payment_state",
        "description": "Inspects current status, debit state, and finality of a payment ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "payment_id": {"type": "string", "description": "The payment attempt identifier (e.g. PAY001)"}
            },
            "required": ["payment_id"],
        },
    },
    {
        "name": "get_attempt_history",
        "description": "Retrieves attempt history across all attempts for an order or payment.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order ID to look up"},
                "payment_id": {"type": "string", "description": "Payment ID to look up"},
            },
        },
    },
    {
        "name": "get_gateway_status",
        "description": "Checks operational status, error rate, and latency of a payment gateway.",
        "parameters": {
            "type": "object",
            "properties": {
                "gateway_name": {"type": "string", "description": "Gateway name, default RAZORPAY"}
            },
        },
    },
    {
        "name": "get_server_health",
        "description": "Inspects server latency, error rate, and whether Financial Safety Mode is active.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "get_webhook_status",
        "description": "Checks whether webhooks have been received and webhook latency for a payment.",
        "parameters": {
            "type": "object",
            "properties": {
                "payment_id": {"type": "string", "description": "Payment ID"}
            },
            "required": ["payment_id"],
        },
    },
    {
        "name": "get_transaction_status",
        "description": "Looks up transaction records across all sessions by transaction ID or payment ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "transaction_id": {"type": "string", "description": "Transaction reference"}
            },
            "required": ["transaction_id"],
        },
    },
    {
        "name": "get_customer_session",
        "description": "Retrieves session metadata, total attempts, and current decision for an order.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order ID"}
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "get_risk_signals",
        "description": "Queries ML model for anomaly score, duplicate risk, and failure risk signals.",
        "parameters": {
            "type": "object",
            "properties": {
                "payment_id": {"type": "string", "description": "Payment ID"}
            },
            "required": ["payment_id"],
        },
    },
    {
        "name": "get_reconciliation_status",
        "description": "Retrieves ledger reconciliation status for an order.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order ID"}
            },
            "required": ["order_id"],
        },
    },
    # Action Tools
    {
        "name": "block_pay_again",
        "description": "Locks the UI 'Pay Again' button to protect against duplicate charge attempts.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order ID to lock UI for"},
                "reason": {"type": "string", "description": "Reason for protective UI lock"},
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "allow_retry",
        "description": "Authorizes a payment retry ONLY when validated against a single-use Recovery Permit.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order ID"},
                "permit_id": {"type": "string", "description": "Valid single-use Recovery Permit ID"},
            },
            "required": ["order_id", "permit_id"],
        },
    },
    {
        "name": "create_recovery_permit",
        "description": "Requests issuance of a single-use recovery permit if conditions are verified safe.",
        "parameters": {
            "type": "object",
            "properties": {
                "payment_id": {"type": "string", "description": "Payment ID"},
                "order_id": {"type": "string", "description": "Order ID"},
                "amount": {"type": "number", "description": "Payment amount"},
                "reason": {"type": "string", "description": "Reason for permit issuance"},
            },
            "required": ["payment_id", "order_id", "amount", "reason"],
        },
    },
    {
        "name": "request_payment_status",
        "description": "Triggers active bank and gateway settlement status inquiry for a payment.",
        "parameters": {
            "type": "object",
            "properties": {
                "payment_id": {"type": "string", "description": "Payment ID to verify"}
            },
            "required": ["payment_id"],
        },
    },
    {
        "name": "trigger_reconciliation",
        "description": "Initiates ledger reconciliation between bank debit and merchant order fulfillment.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order ID to reconcile"}
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "switch_gateway",
        "description": "Switches the gateway route for subsequent attempts if primary gateway is degraded.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order ID"},
                "new_gateway": {"type": "string", "description": "Target gateway name"},
            },
            "required": ["order_id", "new_gateway"],
        },
    },
    {
        "name": "create_support_case",
        "description": "Escalates payment conflict or anomaly to human support and compliance teams.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order ID"},
                "reason": {"type": "string", "description": "Reason for human escalation"},
            },
            "required": ["order_id", "reason"],
        },
    },
    {
        "name": "trigger_eligible_refund",
        "description": "Queues duplicate or erroneous debit for automated refund execution.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order ID"},
                "payment_id": {"type": "string", "description": "Payment ID"},
                "amount": {"type": "number", "description": "Refund amount"},
                "reason": {"type": "string", "description": "Refund justification"},
            },
            "required": ["order_id", "payment_id", "amount", "reason"],
        },
    },
    {
        "name": "notify_user",
        "description": "Sends customer-facing notification regarding payment progress or warnings.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "Customer ID"},
                "message": {"type": "string", "description": "Notification text"},
                "level": {"type": "string", "description": "INFO, WARNING, SUCCESS, or ERROR"},
            },
            "required": ["user_id", "message"],
        },
    },
    {
        "name": "notify_merchant",
        "description": "Sends fulfillment or settlement confirmation to merchant systems.",
        "parameters": {
            "type": "object",
            "properties": {
                "merchant_id": {"type": "string", "description": "Merchant ID"},
                "order_id": {"type": "string", "description": "Order ID"},
                "status": {"type": "string", "description": "Order status update"},
            },
            "required": ["merchant_id", "order_id", "status"],
        },
    },
    # Monitoring Tools
    {
        "name": "watch_payment",
        "description": "Checks continuous monitoring status of an in-flight payment.",
        "parameters": {
            "type": "object",
            "properties": {
                "payment_id": {"type": "string", "description": "Payment ID"}
            },
            "required": ["payment_id"],
        },
    },
    {
        "name": "watch_gateway",
        "description": "Polls gateway latency and operational health.",
        "parameters": {
            "type": "object",
            "properties": {
                "gateway_name": {"type": "string", "description": "Gateway name"}
            },
        },
    },
    {
        "name": "watch_server",
        "description": "Polls server latency and circuit breaker status.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "watch_webhook",
        "description": "Polls webhook delivery status for a payment.",
        "parameters": {
            "type": "object",
            "properties": {
                "payment_id": {"type": "string", "description": "Payment ID"}
            },
            "required": ["payment_id"],
        },
    },
    {
        "name": "watch_reconciliation",
        "description": "Polls reconciliation progress for an order.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order ID"}
            },
            "required": ["order_id"],
        },
    },
]


class ToolDispatcher:
    """
    Central execution gate for all AI-requested and system tool calls.
    Enforces schema validation, authorization, and safety policy checking.
    """

    @classmethod
    def validate_and_execute(
        cls,
        tool_name: str,
        arguments: Dict[str, Any],
        context_payment_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes a requested tool call after rigorous validation:
        1. Whitelist validation (rejects arbitrary system/shell execution).
        2. Parameter schema validation.
        3. Financial safety policy authorization for action tools.
        4. Structured audit logging.
        """
        # 1. Whitelist Check
        if tool_name not in ALLOWED_TOOLS:
            logger.warning(f"Unauthorized tool requested: {tool_name}")
            return {
                "status": "UNAUTHORIZED_TOOL",
                "tool_name": tool_name,
                "error": f"Tool '{tool_name}' is not in the allowed AUREV tool registry.",
            }

        func = ALLOWED_TOOLS[tool_name]

        # 2. Safety Authorization for Action Tools
        if tool_name in ACTION_TOOLS:
            permitted, denial_reason = cls._check_action_safety(
                tool_name=tool_name,
                arguments=arguments,
                context_payment_id=context_payment_id,
            )
            if not permitted:
                logger.warning(f"Safety Gate blocked action '{tool_name}': {denial_reason}")
                payment_id = arguments.get("payment_id") or context_payment_id or "UNKNOWN"
                order_id = arguments.get("order_id") or "UNKNOWN"
                timeline_store.record_event(
                    payment_id=payment_id,
                    order_id=order_id,
                    event_type=EventType.RETRY_BLOCKED,
                    source="safety_gate",
                    status="ACTION_DENIED",
                    metadata={"tool": tool_name, "reason": denial_reason},
                )
                return {
                    "status": "ACTION_DENIED",
                    "tool_name": tool_name,
                    "allowed": False,
                    "reason": denial_reason,
                }

        # 3. Parameter Alignment & Execution
        try:
            sig = inspect.signature(func)
            valid_args = {}
            for param_name, param in sig.parameters.items():
                if param_name in arguments:
                    valid_args[param_name] = arguments[param_name]
                elif param.default is inspect.Parameter.empty:
                    return {
                        "status": "INVALID_ARGUMENTS",
                        "tool_name": tool_name,
                        "error": f"Missing required parameter '{param_name}' for tool '{tool_name}'.",
                    }

            result = func(**valid_args)

            # Audit record for action tools
            if tool_name in ACTION_TOOLS:
                payment_id = arguments.get("payment_id") or context_payment_id or "UNKNOWN"
                order_id = arguments.get("order_id") or "UNKNOWN"
                timeline_store.record_event(
                    payment_id=payment_id,
                    order_id=order_id,
                    event_type=EventType.AUREV_DECISION,
                    source="tool_dispatcher",
                    status=f"EXECUTED_{tool_name.upper()}",
                    metadata={"tool": tool_name, "arguments": arguments},
                )

            # Normalize return value
            if isinstance(result, dict):
                return {"status": "SUCCESS", "tool_name": tool_name, "result": result}
            elif hasattr(result, "model_dump"):
                return {"status": "SUCCESS", "tool_name": tool_name, "result": result.model_dump()}
            return {"status": "SUCCESS", "tool_name": tool_name, "result": result}

        except Exception as exc:
            logger.error(f"Error executing tool '{tool_name}': {exc}", exc_info=True)
            return {
                "status": "EXECUTION_ERROR",
                "tool_name": tool_name,
                "error": str(exc),
            }

    @classmethod
    def _check_action_safety(
        cls,
        tool_name: str,
        arguments: Dict[str, Any],
        context_payment_id: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Applies deterministic financial safety policy to action tools.
        Gemini cannot execute an unsafe action directly.
        """
        order_id = arguments.get("order_id")
        payment_id = arguments.get("payment_id") or context_payment_id
        session = None

        if order_id:
            session = payment_memory.get_session_by_order_id(order_id)
        elif payment_id:
            session = payment_memory.get_session_by_payment_id(payment_id)

        # 1. allow_retry safety validation
        if tool_name == "allow_retry":
            permit_id = arguments.get("permit_id")
            if not permit_id:
                return False, "Retry prohibited: Missing required Recovery Permit ID."

            if not session:
                return False, f"Retry prohibited: Order session '{order_id}' not found."

            if _system_health.is_safety_mode_active:
                return False, "Retry prohibited: System is in Financial Safety Mode. All retries are suspended."

            if session.has_debited_attempt():
                return False, "Retry prohibited: Customer bank account was debited on a prior attempt."

            if session.has_successful_attempt():
                return False, f"Retry prohibited: Order '{session.order_id}' already has a successful payment."

            permit = payment_memory.get_permit(permit_id)
            if not permit:
                return False, f"Retry prohibited: Recovery permit '{permit_id}' is invalid or does not exist."
            if permit.status.value != "ACTIVE":
                return False, f"Retry prohibited: Recovery permit '{permit_id}' is not ACTIVE (status: {permit.status.value})."

        # 2. create_recovery_permit safety validation
        elif tool_name == "create_recovery_permit":
            if not session and order_id:
                session = payment_memory.get_session_by_order_id(order_id)

            if _system_health.is_safety_mode_active:
                return False, "Permit creation rejected: System is in Financial Safety Mode."

            if session:
                if session.has_debited_attempt():
                    return False, "Permit creation rejected: Customer was debited. Issue refund or reconcile instead of permitting retry."
                if session.has_successful_attempt():
                    return False, "Permit creation rejected: Order is already paid."
                if session.finality_state == FinalityState.UNKNOWN:
                    return False, "Permit creation rejected: Original transaction remains unresolved in UNKNOWN state."

        # 3. trigger_eligible_refund safety validation
        elif tool_name == "trigger_eligible_refund":
            amount = arguments.get("amount", 0.0)
            if amount <= 0.0:
                return False, f"Refund rejected: Invalid amount ({amount})."

        return True, "Action approved by Safety Gate."
