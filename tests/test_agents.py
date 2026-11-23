import os, tempfile, unittest
os.environ['DATABASE_PATH'] = os.path.join(tempfile.gettempdir(),'netwatch_m2_test.db')
from agents.supervisor import SupervisorAgent
from llm.client import GeminiClient

class AgentWorkflowTests(unittest.TestCase):
    def setUp(self): self.supervisor=SupervisorAgent(llm=GeminiClient(api_key=''))
    def test_missing_customer_id_pauses(self):
        out=self.supervisor.run('My internet is not working')
        self.assertEqual(out['result']['status'],'needs_customer_id')
    def test_active_pune_customer_pending_confirmation(self):
        out=self.supervisor.run('Internet not working, customer ID C1001')
        self.assertEqual(out['result']['status'],'pending_customer')
        self.assertEqual(out['result']['customer']['name'],'Rahul Sharma')
        self.assertTrue(any(e['agent']=='Memory Agent' for e in out['events']))
    def test_mumbai_outage_escalates(self):
        out=self.supervisor.run('Internet is down, customer ID C1004')
        self.assertEqual(out['result']['status'],'escalated')
        self.assertTrue(out['result']['verification']['ticket'])
    def test_suspended_account_escalates(self):
        out=self.supervisor.run('Internet is not working, customer ID C1003')
        self.assertEqual(out['result']['status'],'escalated')

if __name__=='__main__': unittest.main()
