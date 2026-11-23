from agents.base import BaseAgent
from llm.prompts import TROUBLESHOOT_SYSTEM
class TroubleshootingAgent(BaseAgent):
    name = "Troubleshooting Agent"
    def run(self, ctx):
        ctx.log(self.name,"started","Preparing safe, evidence-based next steps.")
        state=ctx.state; account=state.get('customer') or {}; diagnosis=state.get('diagnosis','')
        if any(term in diagnosis.lower() for term in ('outage','account issue','service-side')):
            steps=["Do not reset the router while a service-side fault or outage is suspected.","Keep the router powered on and wait for the support team update."]
        elif account.get('router_status')=='Offline':
            steps=["Check that the router power adapter is connected to a working outlet.","Check whether the router power indicator turns on.","If it remains offline, do not open the device; request technical support."]
        elif 'wan' in diagnosis.lower() and 'fault' in diagnosis.lower():
            steps=["Check that the WAN/Internet cable is firmly connected at accessible ends.","Observe and report the WAN/Internet indicator colour.","Do not open the router or alter advanced settings; the service team may need to investigate the line."]
        else:
            steps=["Check that the WAN/Internet cable is firmly connected at both accessible ends.","Observe whether the WAN/Internet indicator is normal or red.","Test the connection on another device to identify whether the issue is device-specific."]
        explanation="Recommendations are based on simulated account and network observations."
        llm_result=None
        if self.llm and self.llm.configured and 'outage' not in diagnosis.lower() and 'account issue' not in diagnosis.lower():
            prompt=f"Issue: {state.get('issue')}\nDiagnosis: {diagnosis}\nEvidence: {state.get('outage_info')}\nWAN probe: {state.get('wan_probe')}\nSafe baseline steps: {steps}"
            try:
                llm_result=self.llm.generate_json(prompt,TROUBLESHOOT_SYSTEM)
                proposed=llm_result.get('steps')
                if isinstance(proposed,list) and proposed: steps=[str(x) for x in proposed[:4]]
                explanation=str(llm_result.get('explanation') or explanation)
            except Exception as exc: ctx.log(self.name,'llm_fallback',str(exc))
        state['recommended_steps']=steps
        result={"steps":steps,"explanation":explanation,"llm_enhancement":llm_result}
        ctx.log(self.name,'completed',result)
        return result
