from agents.base import BaseAgent
from llm.prompts import INTENT_SYSTEM
from tools.account_tools import retrieve_account
import re
class CustomerAgent(BaseAgent):
    name = "Customer Agent"
    def run(self, ctx):
        ctx.log(self.name,"started","Extracting customer intent and account reference.")
        text = ctx.customer_message
        extracted = {"issue_summary":text,"intent":"internet_down","customer_id":None,"urgency":"medium","missing_information":[]}
        if self.llm and self.llm.configured:
            try: extracted = {**extracted, **self.llm.generate_json(text, INTENT_SYSTEM)}
            except Exception as exc: ctx.log(self.name,"llm_fallback",str(exc))
        match = re.search(r'\bC\d{4}\b', text.upper())
        candidate_id = str(extracted.get('customer_id') or '').upper()
        customer_id = candidate_id if re.fullmatch(r'C\d{4}', candidate_id) else (match.group(0) if match else None)
        if customer_id:
            lookup = retrieve_account(customer_id)
            ctx.state['customer_id'] = customer_id.upper()
            ctx.state['account_lookup'] = lookup
            if lookup['success']: ctx.state['customer'] = lookup['account']
        ctx.state['issue'] = extracted.get('issue_summary') or text
        ctx.state['intent'] = extracted.get('intent','other')
        ctx.state['urgency'] = extracted.get('urgency','medium')
        ctx.log(self.name,"completed",{"customer_id":customer_id,"intent":ctx.state['intent']})
        return extracted
