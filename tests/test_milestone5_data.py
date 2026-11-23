import os
import tempfile
import unittest
from config import settings

TEST_DB = os.path.join(tempfile.gettempdir(), "netwatch_m5_data_test.db")
object.__setattr__(settings, "database_path", TEST_DB)
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

from data.generator import ensure_dataset, dataset_summary, generate_network_events
from tools.account_tools import retrieve_account
from memory.database import connect
from agents.supervisor import SupervisorAgent
from llm.client import GeminiClient


class SyntheticDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        object.__setattr__(settings, "database_path", TEST_DB)
        ensure_dataset(target_customers=1000, target_events=5000, target_cases=500, seed=20261123)

    def setUp(self):
        object.__setattr__(settings, "database_path", TEST_DB)

    def test_initial_dataset_targets_and_original_fixtures(self):
        counts = ensure_dataset(target_customers=1000, target_events=5000, target_cases=500, seed=20261123)
        self.assertEqual(counts["customers"], 1000)
        self.assertEqual(counts["devices"], 1000)
        self.assertEqual(counts["events"], 5000)
        self.assertEqual(counts["historical_cases"], 500)
        self.assertEqual(retrieve_account("C1001")["account"]["name"], "Rahul Sharma")
        self.assertEqual(retrieve_account("C1004")["account"]["area"], "Mumbai")

    def test_generated_customer_lookup(self):
        account = retrieve_account("C1005")
        self.assertTrue(account["success"])
        self.assertTrue(account["account"]["name"])

    def test_generation_is_idempotent(self):
        before = dataset_summary()["counts"]
        after = ensure_dataset(target_customers=1000, target_events=5000, target_cases=500, seed=999)
        self.assertEqual(before, after)

    def test_runtime_events_append_without_deleting(self):
        before = dataset_summary()["counts"]["events"]
        self.assertEqual(generate_network_events(37, seed=42), 37)
        after = dataset_summary()["counts"]["events"]
        self.assertEqual(after, before + 37)


    def test_all_one_thousand_customers_are_lookupable(self):
        with connect() as conn:
            ids = [r[0] for r in conn.execute("SELECT customer_id FROM customers").fetchall()]
        self.assertEqual(len(ids), 1000)
        self.assertTrue(all(retrieve_account(cid)["success"] for cid in ids))

    def test_generated_customer_runs_through_agent_workflow(self):
        supervisor = SupervisorAgent(llm=GeminiClient(api_key=""))
        output = supervisor.run("Internet is not working. Customer ID C1005", conversation_id="m5gen1005")
        self.assertIn(output["result"]["status"], {"pending_customer", "escalated"})
        self.assertEqual(output["result"]["customer"]["name"], retrieve_account("C1005")["account"]["name"])

    def test_relational_integrity(self):
        with connect() as conn:
            orphan_devices = conn.execute("""SELECT COUNT(*) FROM network_devices d LEFT JOIN customers c
                ON d.customer_id=c.customer_id WHERE c.customer_id IS NULL""").fetchone()[0]
            orphan_events = conn.execute("""SELECT COUNT(*) FROM network_events e LEFT JOIN customers c
                ON e.customer_id=c.customer_id WHERE c.customer_id IS NULL""").fetchone()[0]
        self.assertEqual(orphan_devices, 0)
        self.assertEqual(orphan_events, 0)


if __name__ == "__main__":
    unittest.main()
