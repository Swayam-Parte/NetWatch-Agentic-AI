"""Interprets customer follow-up feedback without making resolution claims."""
from agents.base import BaseAgent

FEEDBACK_PROMPT = """Classify the customer's latest support follow-up using the prior context.
Return JSON only with keys: feedback (one of resolved, unresolved, action_completed, unclear),
customer_confirmed_resolved (boolean), new_evidence (array of short factual observations),
summary (string). Only use resolved when the customer explicitly says internet/service works again.
Do not treat 'I restarted it' as resolution."""


class FeedbackAgent(BaseAgent):
    name = "Customer Feedback Agent"

    def run(self, ctx, explicit_resolved=False):
        text = (ctx.customer_message or "").strip()
        lowered = text.lower()
        fallback = {"feedback": "unclear", "customer_confirmed_resolved": False,
                    "new_evidence": [], "summary": text}
        if explicit_resolved or any(p in lowered for p in (
            "it's working", "it is working", "internet is working", "connection is back",
            "fixed now", "problem is fixed", "resolved now", "works now", "working again")):
            fallback.update(feedback="resolved", customer_confirmed_resolved=True)
        elif any(p in lowered for p in (
            "still not working", "still not fixed", "not resolved", "same issue",
            "no internet", "didn't work", "did not work", "not working yet")):
            fallback.update(feedback="unresolved", new_evidence=[text])
        elif any(p in lowered for p in ("restarted", "rebooted", "checked the cable", "wan light", "tried that", "done")):
            fallback.update(feedback="action_completed", new_evidence=[text])
        result = fallback
        if self.llm and self.llm.configured:
            try:
                prior = ctx.state.get("last_recommendations", [])
                prompt = f"Previous recommendations: {prior}\nPrevious diagnosis: {ctx.state.get('diagnosis')}\nCustomer follow-up: {text}"
                model_result = self.llm.generate_json(prompt, FEEDBACK_PROMPT)
                if model_result.get("feedback") in {"resolved", "unresolved", "action_completed", "unclear"}:
                    result = {**fallback, **model_result}
                    # Resolution always requires explicit confirmation in the actual message or UI.
                    result["customer_confirmed_resolved"] = bool(
                        fallback["customer_confirmed_resolved"] or
                        (model_result.get("customer_confirmed_resolved") and
                         model_result.get("feedback") == "resolved" and
                         any(p in lowered for p in ("working", "fixed", "resolved", "back online", "connected")))
                    )
            except Exception as exc:
                ctx.log(self.name, "llm_fallback", str(exc))
        if explicit_resolved:
            result.update(feedback="resolved", customer_confirmed_resolved=True)
        ctx.state["customer_feedback"] = result
        ctx.log(self.name, "completed", result)
        return result
