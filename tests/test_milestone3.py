import os, tempfile, unittest
from unittest.mock import patch
os.environ['DATABASE_PATH']=os.path.join(tempfile.gettempdir(),'netwatch_m3_test.db')
from agents.supervisor import SupervisorAgent
from llm.client import GeminiClient
from memory.database import initialize_database, load_conversation, get_messages
from config import settings

class Milestone3Tests(unittest.TestCase):
    def setUp(self):
        object.__setattr__(settings, "database_path", os.environ["DATABASE_PATH"])
        if os.path.exists(os.environ['DATABASE_PATH']): os.remove(os.environ['DATABASE_PATH'])
        initialize_database(); self.agent=SupervisorAgent(llm=GeminiClient(api_key=''))
    def test_conversation_persists_customer_and_messages(self):
        first=self.agent.run('Internet is not working. Customer ID C1001',conversation_id='persist01')
        second=self.agent.run('Still not working',conversation_id='persist01')
        saved=load_conversation('persist01')
        self.assertEqual(saved['customer_id'],'C1001')
        self.assertEqual(saved['attempts'],1)
        self.assertEqual(len(get_messages('persist01')),4)
        self.assertEqual(second['result']['status'],'pending_customer')
    def test_explicit_resolution_closes_case(self):
        self.agent.run('Internet not working customer ID C1001',conversation_id='resolve01')
        out=self.agent.run('The internet is working again now',conversation_id='resolve01')
        self.assertEqual(out['result']['status'],'resolved')
    def test_unresolved_feedback_replans_on_conflicting_wan_evidence(self):
        self.agent.run('Internet not working customer ID C1001',conversation_id='replan01')
        out=self.agent.run('Still not working after checking the cable',conversation_id='replan01')
        self.assertTrue(any(e['event']=='replanned' for e in out['events']))
        self.assertIn('WAN cable',out['result']['diagnosis']['tool_diagnosis']['diagnosis'])
    def test_tool_failure_retries_once(self):
        self.agent.run('Internet not working customer ID C1001',conversation_id='retry01')
        with patch('agents.supervisor.check_outage',side_effect=[RuntimeError('temporary'), {'success':True,'outage':False,'severity':'None','message':'OK'}]):
            out=self.agent.run('Still not working',conversation_id='retry01')
        self.assertTrue(any(e['event']=='tool_retry' for e in out['events']))
        self.assertTrue(any(e['event']=='tool_check_succeeded' for e in out['events']))
    def test_max_attempts_escalates(self):
        self.agent.run('Internet not working customer ID C1001',conversation_id='limit01')
        self.agent.run('Still not working',conversation_id='limit01')
        self.agent.run('Still no internet',conversation_id='limit01')
        out=self.agent.run('Still not working',conversation_id='limit01')
        self.assertEqual(out['result']['status'],'escalated')
        self.assertIsNotNone(out['result']['verification']['ticket'])

if __name__=='__main__': unittest.main()
