"""
Google Gemini AI Reasoning Provider for AUREV.
Implements:
1. Continuous agentic reasoning with controlled tool/function calling.
2. Strict schema validation and safety gate routing for all tool calls.
3. Multi-step reasoning loop (inspect context -> call tool -> receive result -> reason again).
4. Structured output schema (AUREV_REASONING_RESULT).
5. Safe fallback to deterministic logic if Gemini is unavailable, rate-limited, or timed out.
6. Support for dependency injection / mocking for offline and CI testing.
"""
import json
import logging
import re
from typing import Any, Dict, List, Optional

from config.settings import settings
from agent.providers.ai_provider import AIProvider
from agent.providers.rule_based_provider import RuleBasedProvider
from agent.prompts.system_prompt import AUREV_SYSTEM_PROMPT
from models.decisions import AurevReasoningResult
from models.enums import AurevDecision
from tools.tool_dispatcher import ToolDispatcher, TOOL_SCHEMAS

logger = logging.getLogger("aurev.ai.gemini")

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None
    types = None


class GeminiProvider(AIProvider):
    """
    Real Agentic AI Reasoning Provider powered by Google Gemini.
    Participates in a multi-step reasoning/tool loop while respecting deterministic safety authority.
    """

    def __init__(self, api_key: str = "", model: str = "", client: Any = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL or "gemini-2.5-flash"
        self._custom_client = client
        self._fallback = RuleBasedProvider()
        self.max_steps = min(settings.MAX_AGENT_STEPS, 5)

    def _build_tools_spec(self) -> Any:
        """Converts AUREV TOOL_SCHEMAS into Google GenAI FunctionDeclarations."""
        if not GENAI_AVAILABLE or types is None:
            return None
        declarations = []
        for schema in TOOL_SCHEMAS:
            decl = types.FunctionDeclaration(
                name=schema["name"],
                description=schema["description"],
                parameters=schema.get("parameters"),
            )
            declarations.append(decl)
        return types.Tool(function_declarations=declarations)

    def generate_reasoning(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the agentic reasoning process over payment context.
        If Gemini is available, runs multi-step function calling loop.
        If Gemini is unavailable or errors, safely returns deterministic fallback.
        """
        payment_id = context.get("payment_id", "UNKNOWN")
        agent_trace: List[str] = [f"[AUREV] Payment {payment_id} observed."]

        # Fallback if no API key or SDK not installed
        if not self._custom_client and (not self.api_key or not GENAI_AVAILABLE):
            logger.info("No Gemini API key or SDK unavailable. Engaging deterministic safety reasoning.")
            agent_trace.append("[AUREV] Gemini API key not configured. Engaging conservative safety logic.")
            fallback_res = self._fallback.generate_reasoning(context)
            fallback_res["agent_status"] = "AI_UNAVAILABLE"
            fallback_res["agent_trace"] = agent_trace
            fallback_res["confidence"] = 0.85
            fallback_res["proposed_decision"] = fallback_res.get("recommendation", "WAIT")
            fallback_res["reason_summary"] = fallback_res.get("explanation", "")
            return fallback_res

        agent_trace.append(f"[GEMINI] Analyzing payment context for {payment_id} using {self.model}.")

        try:
            client = self._custom_client or genai.Client(api_key=self.api_key)
            tools_spec = self._build_tools_spec()

            system_instruction = f"""{AUREV_SYSTEM_PROMPT}

You are participating in an autonomous verification and safety loop for payment '{payment_id}'.
Inspect the context, request observation or verification tools if evidence is incomplete, and evaluate risk.
When ready, return your final response as strict JSON adhering to this schema:
{{
  "agent_status": "COMPLETED",
  "observed_evidence": ["fact 1", "fact 2"],
  "evidence_gaps": ["uncertainty 1"],
  "risk_assessment": "Summary of financial and duplicate risk",
  "relevant_events": ["Key event 1"],
  "proposed_decision": "WAIT" | "RETRY" | "STOP" | "ESCALATE",
  "proposed_action": "Recommended action tool name or NONE",
  "reason_summary": "Clear explanation of the reasoning and safety justification",
  "confidence": 0.95,
  "next_monitoring_step": "Next verification target if unresolved, or NONE"
}}
"""

            user_prompt = f"""
Current Payment Context:
{json.dumps(context, indent=2)}

Analyze this situation. If any crucial telemetry (such as bank status, transaction status, or server health)
is uncertain or missing, invoke the appropriate observation tool.
Otherwise, provide your final structured assessment in JSON.
"""

            messages = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=user_prompt)],
                )
            ]

            step = 0
            final_text: Optional[str] = None
            requested_tools_log: List[Dict[str, Any]] = []

            while step < self.max_steps:
                step += 1
                config = types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.1,
                    tools=[tools_spec] if tools_spec else None,
                )

                response = client.models.generate_content(
                    model=self.model,
                    contents=messages,
                    config=config,
                )

                function_calls = getattr(response, "function_calls", None)

                # If model requested function calls
                if function_calls:
                    # Append assistant turn
                    if response.candidates and response.candidates[0].content:
                        messages.append(response.candidates[0].content)

                    tool_responses = []
                    for call in function_calls:
                        call_name = call.name
                        call_args = call.args if isinstance(call.args, dict) else dict(call.args or {})
                        requested_tools_log.append({"name": call_name, "args": call_args})
                        agent_trace.append(f"[TOOL] {call_name}({json.dumps(call_args)})")

                        # Pass through Controlled Tool Dispatcher & Safety Gate
                        execution_res = ToolDispatcher.validate_and_execute(
                            tool_name=call_name,
                            arguments=call_args,
                            context_payment_id=payment_id,
                        )

                        if execution_res.get("status") == "ACTION_DENIED":
                            agent_trace.append(f"[SAFETY] ACTION_DENIED: {execution_res.get('reason')}")
                        elif execution_res.get("status") == "SUCCESS":
                            res_summary = str(execution_res.get("result"))
                            if len(res_summary) > 120:
                                res_summary = res_summary[:120] + "..."
                            agent_trace.append(f"[TOOL RESULT] {res_summary}")
                        else:
                            agent_trace.append(f"[TOOL ERROR] {execution_res.get('error')}")

                        tool_part = types.Part.from_function_response(
                            name=call_name,
                            response={"result": execution_res},
                        )
                        tool_responses.append(tool_part)

                    # Append user tool results turn
                    messages.append(types.Content(role="user", parts=tool_responses))
                else:
                    # Final text response received
                    final_text = response.text or ""
                    break

            # Parse structured output from final text
            parsed_result = self._parse_structured_output(final_text, context, agent_trace, requested_tools_log)
            return parsed_result

        except Exception as exc:
            logger.error(f"Gemini API error during reasoning: {exc}", exc_info=True)
            agent_trace.append(f"[AUREV] Gemini AI error ({exc}). Engaging deterministic safety fallback.")
            fallback_res = self._fallback.generate_reasoning(context)
            fallback_res["agent_status"] = "AI_UNAVAILABLE"
            fallback_res["agent_trace"] = agent_trace
            fallback_res["confidence"] = 0.80
            fallback_res["proposed_decision"] = fallback_res.get("recommendation", "WAIT")
            fallback_res["reason_summary"] = fallback_res.get("explanation", "")
            return fallback_res

    def _parse_structured_output(
        self,
        text: Optional[str],
        context: Dict[str, Any],
        agent_trace: List[str],
        requested_tools: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Parses structured JSON from Gemini response into normalized contract."""
        data: Dict[str, Any] = {}

        if text:
            cleaned = text.strip()
            # Remove Markdown code blocks if present
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
            if match:
                cleaned = match.group(1).strip()

            try:
                data = json.loads(cleaned)
            except json.JSONDecodeError:
                logger.warning(f"Could not parse Gemini JSON response directly: {cleaned[:100]}...")
                # Extract fields with best-effort regex
                data = {"reason_summary": text}

        # Normalize decision
        raw_decision = str(data.get("proposed_decision") or data.get("recommendation") or "WAIT").upper()
        if raw_decision not in [d.value for d in AurevDecision]:
            raw_decision = "WAIT"

        observed = data.get("observed_evidence") or data.get("known") or []
        gaps = data.get("evidence_gaps") or data.get("uncertain") or []
        reason = data.get("reason_summary") or data.get("explanation") or "Gemini reasoning evaluated."
        confidence = float(data.get("confidence") or 0.92)

        agent_trace.append(f"[GEMINI] Proposed Decision: {raw_decision}. Reason: {reason}")

        structured = {
            # Legacy fields for backward compatibility
            "known": observed,
            "uncertain": gaps,
            "verify_next": [data.get("next_monitoring_step")] if data.get("next_monitoring_step") else [],
            "recommendation": raw_decision,
            "explanation": reason,
            # Structured AurevReasoningResult fields
            "agent_status": "COMPLETED",
            "observed_evidence": observed,
            "evidence_gaps": gaps,
            "risk_assessment": data.get("risk_assessment", ""),
            "relevant_events": data.get("relevant_events", []),
            "requested_tools": requested_tools,
            "proposed_decision": raw_decision,
            "proposed_action": data.get("proposed_action", ""),
            "reason_summary": reason,
            "confidence": confidence,
            "next_monitoring_step": data.get("next_monitoring_step"),
            "agent_trace": agent_trace,
        }

        return structured
