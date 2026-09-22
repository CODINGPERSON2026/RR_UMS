"""
Automated unit and integration tests for Adjutant Recommendation and 2IC Executive Decision Workflow.
Uses a lightweight test Flask app registering company_rec_bp directly.
"""

import os
import sys
import unittest
import json
from flask import Flask

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from db_config import get_db_connection
from aiml.ai_new_joinee_recommendation.routes import company_rec_bp, ensure_recommendations_table

def create_test_app():
    test_app = Flask(__name__)
    test_app.secret_key = "test-secret-key"
    test_app.register_blueprint(company_rec_bp)
    return test_app

class TestAdjutantAnd2ICWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.flask_app = create_test_app()

    def setUp(self):
        self.client = self.flask_app.test_client()

        conn = get_db_connection()
        self.assertIsNotNone(conn, "Database connection failed")
        cursor = conn.cursor(dictionary=True)
        ensure_recommendations_table(cursor, conn)

        self.test_army_no = "TEST_ADJ_9999"
        cursor.execute("DELETE FROM ai_new_joinee_recommendations WHERE army_number = %s", (self.test_army_no,))
        cursor.execute("""
            INSERT INTO ai_new_joinee_recommendations (
                army_number, name, `rank`, trade,
                recommended_company, recommended_position, confidence_score, recommendation_percentage,
                decision_type, created_at, updated_at
            ) VALUES (
                %s, 'Test Soldier', 'L NK', 'TTC',
                'HQ Coy', 'GD', '88.5%', 88.5,
                'pending', NOW(), NOW()
            )
        """, (self.test_army_no,))
        conn.commit()
        cursor.execute("SELECT id FROM ai_new_joinee_recommendations WHERE army_number = %s", (self.test_army_no,))
        row = cursor.fetchone()
        self.test_rec_id = row["id"]
        cursor.close()
        conn.close()

    def tearDown(self):
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ai_new_joinee_recommendations WHERE army_number = %s", (self.test_army_no,))
            conn.commit()
            cursor.close()
            conn.close()

    def test_01_adjutant_update_without_reason_fails(self):
        """Adjutant updating recommendation without a reason must be rejected with 400."""
        with self.client.session_transaction() as sess:
            sess["role"] = "ADJUTANT"
            sess["username"] = "Adjutant Officer"
            sess["user_id"] = "101"

        res = self.client.post("/api/ai/company-recommendation/decision",
            data=json.dumps({
                "id": self.test_rec_id,
                "action": "adjutant_update",
                "final_company": "COMN COY",
                "final_section": "COMMUNICATION / TECHNICAL",
                "final_position": "Radio RR",
                "decision_remarks": ""  # Missing reason!
            }),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data)
        self.assertFalse(data.get("success"))
        self.assertIn("Reason is required", data.get("error", ""))

    def test_02_adjutant_update_with_reason_succeeds_without_assigning(self):
        """Adjutant updating recommendation with reason records proposal but does NOT assign."""
        with self.client.session_transaction() as sess:
            sess["role"] = "ADJUTANT"
            sess["username"] = "Adjutant Officer"
            sess["user_id"] = "101"

        res = self.client.post("/api/ai/company-recommendation/decision",
            data=json.dumps({
                "id": self.test_rec_id,
                "action": "adjutant_update",
                "final_company": "COMN COY",
                "final_section": "COMMUNICATION / TECHNICAL",
                "final_position": "Radio RR",
                "decision_remarks": "Critical shortage of radio operators in COMN COY"
            }),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("adjutant_action"), "updated")
        self.assertEqual(data.get("adjutant_company"), "COMN COY")
        self.assertEqual(data.get("adjutant_position"), "Radio RR")

        # Verify in database: Adjutant proposal recorded, but decision_type is still pending (not assigned!)
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM ai_new_joinee_recommendations WHERE id = %s", (self.test_rec_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        self.assertEqual(row["adjutant_action"], "updated")
        self.assertEqual(row["adjutant_company"], "COMN COY")
        self.assertEqual(row["adjutant_section"], "COMMUNICATION / TECHNICAL")
        self.assertEqual(row["adjutant_position"], "Radio RR")
        self.assertEqual(row["adjutant_remarks"], "Critical shortage of radio operators in COMN COY")
        self.assertEqual(row["adjutant_by"], "Adjutant Officer")
        self.assertNotEqual(row["decision_type"], "accepted", "Adjutant must never set decision_type to accepted!")

    def test_03_insight_detail_returns_adjutant_proposal_to_2ic(self):
        """2IC viewing insight detail must see Adjutant's proposal and remarks."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE ai_new_joinee_recommendations
            SET adjutant_action = 'updated',
                adjutant_company = '3 COY',
                adjutant_section = 'TECHNICAL / CORPS HQ',
                adjutant_position = 'Corps HQ',
                adjutant_remarks = 'Recommended for specialized electronic node',
                adjutant_by = 'Capt Sharma (Adjutant)',
                adjutant_at = NOW()
            WHERE id = %s
        """, (self.test_rec_id,))
        conn.commit()
        cursor.close()
        conn.close()

        with self.client.session_transaction() as sess:
            sess["role"] = "2IC"
            sess["username"] = "Lt Col Verma"
            sess["user_id"] = "102"

        res = self.client.get(f"/api/ai/company-recommendation/insights/{self.test_rec_id}")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data.get("success"))
        item = data.get("data")
        self.assertEqual(item["adjutant_action"], "updated")
        self.assertEqual(item["adjutant_company"], "3 COY")
        self.assertEqual(item["adjutant_position"], "Corps HQ")
        self.assertEqual(item["adjutant_remarks"], "Recommended for specialized electronic node")
        self.assertEqual(item["adjutant_by"], "Capt Sharma (Adjutant)")
        self.assertTrue(item["can_assign_company"], "2IC must have assignment authority")

    def test_04_2ic_accept_assigns_placement(self):
        """2IC accepting recommendation updates final assignment and status to accepted."""
        with self.client.session_transaction() as sess:
            sess["role"] = "2IC"
            sess["username"] = "Lt Col Verma"
            sess["user_id"] = "102"

        res = self.client.post("/api/ai/company-recommendation/decision",
            data=json.dumps({
                "id": self.test_rec_id,
                "action": "accept",
                "final_company": "COMN COY",
                "final_section": "COMMUNICATION / TECHNICAL",
                "final_position": "Radio RR",
                "decision_remarks": "Approved as proposed by Adjutant"
            }),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("decision_type"), "accepted")

        # Verify in DB
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM ai_new_joinee_recommendations WHERE id = %s", (self.test_rec_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        self.assertEqual(row["decision_type"], "accepted")
        self.assertEqual(row["final_company"], "COMN COY")
        self.assertEqual(row["final_position"], "Radio RR")
        self.assertIn("Lt Col Verma", row["decided_by"])

if __name__ == "__main__":
    unittest.main()
