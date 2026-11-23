from agents.base import BaseAgent
from agents.feedback_agent import FeedbackAgent
from agents.base import AgentContext
from agents.feedback_agent import FEEDBACK_PROMPT
from llm.prompts import VERIFY_SYSTEM
from tools.ticket_tools import create_support_ticket
from config import settings

class VerificationAgent(BaseAgent):
    name = "Verification & Escalation Agent"
    def run(self, ctx, customer_confirmed_resolved=False):
        ctx.log(self.name,"started","Checking customer confirmation, attempt limit and escalation conditions.")
        state=ctx.state; diagnosis=state.get('diagnosis','')
        attempts=int(state.get('attempts',0))
        if customer_confirmed_resolved:
            decision={"status":"resolved","reason":"Customer explicitly confirmed service restoration.","next_action":"Close case"}
        elif ('outage' in diagnosis.lower() or 'account issue' in diagnosis.lower() or
              'unavailable' in diagnosis.lower() or attempts >= settings.max_troubleshooting_attempts):
            why = "Maximum troubleshooting attempts reached." if attempts >= settings.max_troubleshooting_attempts else "Service-side outage, account restriction or unavailable account evidence requires support-team intervention."
            decision={"status":"escalated","reason":why,"next_action":"Create support ticket"}
        else:
            decision={"status":"pending_customer","reason":"Customer confirmation is required after trying the recommended steps.","next_action":"Ask customer to test connection and report result"}
        llm_view=None
        if self.llm and self.llm.configured:
            prompt=f"Diagnosis: {diagnosis}\nCustomer confirmed resolved: {customer_confirmed_resolved}\nDeterministic decision: {decision}"
            try: llm_view=self.llm.generate_json(prompt,VERIFY_SYSTEM)
            except Exception as exc: ctx.log(self.name,"llm_fallback",str(exc))
        state['verification']=decision
        if decision['status']=='escalated' and not state.get('ticket'):
            ticket=create_support_ticket(state,decision['reason']); state['ticket']=ticket
        ctx.log(self.name,"completed",{"decision":decision,"llm_review":llm_view})
        return {"decision":decision,"ticket":state.get('ticket'),"llm_review":llm_view}
