"""Supervisor with persistent conversation state, bounded retries and evidence-based replanning."""
from uuid import uuid4
from agents.base import AgentContext
from agents.customer_agent import CustomerAgent
from agents.diagnosis_agent import DiagnosisAgent
from agents.feedback_agent import FeedbackAgent
from agents.memory_agent import MemoryAgent
from agents.troubleshooting_agent import TroubleshootingAgent
from agents.verification_agent import VerificationAgent
from llm.client import GeminiClient
from memory.database import (initialize_database, load_conversation, save_conversation,
                              add_message)
from tools.network_tools import check_outage, probe_wan, diagnose_connection
from config import settings

class SupervisorAgent:
    def __init__(self, llm=None):
        self.llm = llm or GeminiClient()
        self.customer_agent=CustomerAgent(self.llm)
        self.feedback_agent=FeedbackAgent(self.llm)
        self.diagnosis_agent=DiagnosisAgent(self.llm)
        self.memory_agent=MemoryAgent(self.llm)
        self.troubleshooting_agent=TroubleshootingAgent(self.llm)
        self.verification_agent=VerificationAgent(self.llm)
        initialize_database()

    def _retry_network_check(self, area, ctx):
        last_error = None
        for attempt in range(1, 3):
            try:
                result = check_outage(area)
                ctx.log("Supervisor Agent", "tool_check_succeeded", {"tool":"check_outage","attempt":attempt,"result":result})
                return result
            except Exception as exc:
                last_error = str(exc)
                ctx.log("Supervisor Agent", "tool_retry", {"tool":"check_outage","attempt":attempt,"error":last_error})
        return {"success":False,"outage":None,"severity":"Unknown","message":f"Network check failed after retry: {last_error}"}

    def run(self, customer_message: str, customer_confirmed_resolved: bool=False, conversation_id: str | None=None):
        conversation_id = conversation_id or uuid4().hex[:12]
        previous = load_conversation(conversation_id)
        prior_state = previous["state"] if previous else {}
        attempts = int(previous.get("attempts", 0)) if previous else 0
        ctx=AgentContext(customer_message=customer_message, state=prior_state)
        ctx.state["attempts"] = attempts
        ctx.state["conversation_id"] = conversation_id
        ctx.log("Supervisor Agent","started",{"conversation_id":conversation_id,"continuation":bool(previous)})
        add_message(conversation_id,"user",customer_message)
        intake=self.customer_agent.run(ctx)
        if not ctx.state.get('customer'):
            result={"status":"needs_customer_id","message":"Please provide a valid customer ID (for example C1001) so NetWatch can retrieve the simulated account.","intake":intake}
            ctx.log("Supervisor Agent","paused",result)
            self._persist(ctx, conversation_id, result, attempts)
            add_message(conversation_id,"assistant",result["message"])
            return self._package(ctx,result,conversation_id)

        feedback = None
        if previous:
            feedback = self.feedback_agent.run(ctx, explicit_resolved=customer_confirmed_resolved)
            if feedback["feedback"] == "resolved" and feedback["customer_confirmed_resolved"]:
                verification=self.verification_agent.run(ctx, customer_confirmed_resolved=True)
                result=self._result(ctx,intake,feedback,verification)
                self._persist(ctx,conversation_id,result,attempts)
                add_message(conversation_id,"assistant","Thanks for confirming. The issue is marked as resolved.")
                return self._package(ctx,result,conversation_id)
            if feedback["feedback"] in {"unresolved","action_completed"}:
                attempts += 1
                ctx.state["attempts"] = attempts
                ctx.log("Supervisor Agent","feedback_received",{"feedback":feedback["feedback"],"attempt":attempts})
                account=ctx.state["customer"]
                outage=self._retry_network_check(account["area"],ctx)
                ctx.state["outage_info"]=outage
                base=diagnose_connection(account,outage)
                if feedback["feedback"] == "unresolved" and not outage.get("outage"):
                    probe=probe_wan(ctx.state.get("customer_id"))
                    ctx.state["wan_probe"]=probe
                    if probe.get("status")=="No Link" and account.get("router_status")=="Online":
                        revised={"diagnosis":"Possible WAN cable or service-side fault","reason":"The simulated WAN probe reports No Link, conflicting with the account snapshot showing the router online.","replanned":True}
                        ctx.state["diagnosis"]=revised["diagnosis"]
                        ctx.log("Supervisor Agent","replanned",{"previous":base,"new":revised,"conflicting_evidence":{"router":account.get("router_status"),"wan_probe":probe}})
                    else:
                        ctx.state["diagnosis"]=base["diagnosis"]
                else:
                    ctx.state["diagnosis"]=base["diagnosis"]
            elif feedback["feedback"] == "unclear":
                result={"status":"awaiting_feedback","message":"Please tell NetWatch whether the connection is restored, or describe what happened after trying the recommended steps.","intake":intake,"feedback":feedback}
                self._persist(ctx,conversation_id,result,attempts)
                add_message(conversation_id,"assistant",result["message"])
                return self._package(ctx,result,conversation_id)

        if not ctx.state.get("diagnosis"):
            diagnosis=self.diagnosis_agent.run(ctx)
        else:
            diagnosis={"tool_diagnosis":{"diagnosis":ctx.state.get("diagnosis"),"reason":"Diagnosis updated using follow-up evidence."},
                       "llm_analysis":ctx.state.get("diagnostic_insight"),"outage_evidence":ctx.state.get("outage_info"),
                       "wan_probe":ctx.state.get("wan_probe")}
        cases=self.memory_agent.run(ctx)
        troubleshooting=self.troubleshooting_agent.run(ctx)
        ctx.state["last_recommendations"]=troubleshooting.get("steps",[])
        verification=self.verification_agent.run(ctx,customer_confirmed_resolved=False)
        result={"status":verification['decision']['status'],"intake":intake,"customer":ctx.state.get('customer'),
                "diagnosis":diagnosis,"similar_cases":cases,"troubleshooting":troubleshooting,
                "verification":verification,"feedback":feedback,"attempts":attempts}
        ctx.log("Supervisor Agent","completed",{"status":result['status'],"attempts":attempts})
        self._persist(ctx,conversation_id,result,attempts)
        assistant_message = ("Your case has been escalated. Ticket: " + str((verification.get("ticket") or {}).get("ticket_id"))) if result["status"]=="escalated" else "Please try the recommended steps and tell NetWatch what happened."
        add_message(conversation_id,"assistant",assistant_message)
        return self._package(ctx,result,conversation_id)

    @staticmethod
    def _result(ctx,intake,feedback,verification):
        return {"status":"resolved","intake":intake,"customer":ctx.state.get("customer"),"diagnosis":{"tool_diagnosis":{"diagnosis":ctx.state.get("diagnosis"),"reason":"Customer confirmed service restoration."}},"similar_cases":ctx.state.get("similar_cases",[]),"troubleshooting":{"steps":ctx.state.get("last_recommendations",[])},"verification":verification,"feedback":feedback,"attempts":ctx.state.get("attempts",0)}

    @staticmethod
    def _persist(ctx,conversation_id,result,attempts):
        status=result.get("status","OPEN").upper()
        save_conversation(conversation_id,ctx.state,status,attempts)

    @staticmethod
    def _package(ctx,result,conversation_id):
        return {"run_id":ctx.run_id,"conversation_id":conversation_id,"result":result,"events":ctx.events}
