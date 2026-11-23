from agents.base import BaseAgent
from llm.prompts import DIAGNOSIS_SYSTEM
from tools.network_tools import check_outage, diagnose_connection, get_recent_event_summary
class DiagnosisAgent(BaseAgent):
    name = "Network Diagnosis Agent"
    def run(self, ctx):
        ctx.log(self.name,"started","Checking simulated network evidence and diagnosing the issue.")
        account = ctx.state.get('customer')
        if not account:
            result = {"diagnosis":"Customer account unavailable","reason":"A valid customer ID is required before diagnosis."}
            ctx.state['diagnosis'] = result['diagnosis']; ctx.state['outage_info'] = None
            return result
        outage = check_outage(account['area'])
        ctx.state['outage_info'] = outage
        event_summary = get_recent_event_summary(customer_id=ctx.state.get("customer_id"), area=account.get("area"), limit=50)
        ctx.state["recent_event_evidence"] = event_summary
        result = diagnose_connection(account, outage, event_summary)
        ctx.state['diagnosis'] = result['diagnosis']
        insight = None
        if self.llm and self.llm.configured:
            prompt = f"Customer issue: {ctx.state.get('issue')}\nAccount snapshot: {account}\nNetwork tool result: {outage}\nRecent synthetic event evidence: {event_summary}\nRule-based diagnosis: {result}"
            try: insight = self.llm.generate_json(prompt, DIAGNOSIS_SYSTEM)
            except Exception as exc: ctx.log(self.name,"llm_fallback",str(exc))
        ctx.state['diagnostic_insight'] = insight
        payload = {"tool_diagnosis":result,"llm_analysis":insight,"outage_evidence":outage,"recent_event_evidence":event_summary}
        ctx.log(self.name,"completed",payload)
        return payload
