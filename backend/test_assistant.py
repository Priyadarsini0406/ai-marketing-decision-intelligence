"""Integration tests for the Admission Assistant chatbot.

Real HTTP server, isolated SQLite database, real login sessions.
Run with the project Python environment: python -m unittest test_assistant -v
"""
import test_support  # must come first: points the app at a temporary database
import json
import os
import socket
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock
from urllib.error import HTTPError
from urllib.request import Request, urlopen

PASSWORD = "AssistantTest123!"
LEAD_ID = "11111111-2222-4333-8444-555555555555"
PROSPECT_ID = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
NO_PREDICTION_ID = "99999999-8888-4777-8666-555555555555"

STORED_SHAP = {
    "model": "lead_conversion_xgboost", "method": "shap.TreeExplainer", "base_value": -0.47,
    "top_positive": [
        {"feature": "Lead Source", "category": "Reference", "shap_value": 0.91, "value": "Reference"},
        {"feature": "City", "category": "Mumbai", "shap_value": 0.25, "value": "Select"},
        {"feature": "TotalVisits", "category": None, "shap_value": 0.12, "value": 5.0},
    ],
    "top_negative": [
        {"feature": "Total Time Spent on Website", "category": None, "shap_value": -0.72, "value": 40},
        {"feature": "Last Activity", "category": "Email Bounced", "shap_value": -0.33, "value": "Email Bounced"},
    ],
}


class AssistantIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous_llm = os.environ.get("ASSISTANT_LLM")
        os.environ["ASSISTANT_LLM"] = "off"  # deterministic answers; the LLM layer is tested separately
        test_support.reset_database()
        from database.connection import SessionLocal
        from database.models import Lead, MLPrediction, StudentEnquiry
        from api.auth import NewUser, create_user
        import uvicorn

        with SessionLocal() as db:
            users = {}
            for key, role in [("manager", "admission_manager"), ("marketing", "marketing_manager"),
                              ("student", "student"), ("other", "student"), ("admin", "admin")]:
                users[key] = create_user(NewUser(name=f"Test {key.title()}", email=f"{key}@assistant.test",
                                                 password=PASSWORD, role=role), db)
            db.add(Lead(id=LEAD_ID, customer_id=PROSPECT_ID, lead_status="Will revert after reading the email",
                        follow_up_status="Pending"))
            db.add(Lead(id=NO_PREDICTION_ID, customer_id="NO-PRED-1"))
            db.add(MLPrediction(id="p1", lead_id=LEAD_ID, conversion_probability=0.8123, admission_probability=0.8123,
                                lead_score="High", segment_cluster=3, segment_name="High Intent · Reference",
                                shap_explanation=STORED_SHAP))
            db.add(StudentEnquiry(id="e1", student_user_id=users["student"].id, course_interested="BCA",
                                  status="Counselling", created_at=time.time(), updated_at=time.time()))
            db.commit()

        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        cls.base = f"http://127.0.0.1:{port}"
        cls.server = uvicorn.Server(uvicorn.Config("main:app", host="127.0.0.1", port=port, log_level="error"))
        cls.thread = threading.Thread(target=cls.server.run, daemon=True)
        cls.thread.start()
        for _ in range(100):
            try:
                urlopen(cls.base, timeout=1).close()
                break
            except OSError:
                time.sleep(.1)
        else:
            cls.server.should_exit = True
            raise RuntimeError("Test server did not start")
        cls.tokens = {key: cls.login(f"{key}@assistant.test") for key in ("manager", "marketing", "student", "other", "admin")}

    @classmethod
    def tearDownClass(cls):
        cls.server.should_exit = True
        cls.thread.join(timeout=10)
        if cls.previous_llm is None:
            os.environ.pop("ASSISTANT_LLM", None)
        else:
            os.environ["ASSISTANT_LLM"] = cls.previous_llm

    @classmethod
    def call(cls, method, path, data=None, token=None):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        body = json.dumps(data).encode() if data is not None else None
        try:
            with urlopen(Request(cls.base + path, data=body, headers=headers, method=method), timeout=60) as res:
                return res.status, json.loads(res.read() or b"null")
        except HTTPError as error:
            return error.code, json.loads(error.read() or b"null")

    @classmethod
    def login(cls, email):
        status, data = cls.call("POST", "/auth/login", {"email": email, "password": PASSWORD})
        assert status == 200, data
        return data["token"]

    def chat(self, who, message, **context):
        payload = {"message": message}
        if context:
            payload["context"] = context
        return self.call("POST", "/assistant/chat", payload, self.tokens[who])

    # ------------------------------------------------------------ access and validation
    def test_requires_sign_in(self):
        for method, path, data in [("POST", "/assistant/chat", {"message": "hi"}), ("GET", "/assistant/history", None),
                                   ("GET", "/assistant/welcome", None), ("DELETE", "/assistant/history", None)]:
            self.assertEqual(self.call(method, path, data)[0], 401, path)

    def test_rejects_invalid_input(self):
        token = self.tokens["manager"]
        self.assertEqual(self.call("POST", "/assistant/chat", {"message": "   "}, token)[0], 422)
        self.assertEqual(self.call("POST", "/assistant/chat", {"message": "x" * 1001}, token)[0], 422)
        self.assertEqual(self.call("POST", "/assistant/chat", {"message": "hi", "extra": 1}, token)[0], 422)
        self.assertEqual(self.call("POST", "/assistant/chat",
                                   {"message": "hi", "context": {"lead_id": "x'; drop table"}}, token)[0], 422)

    def test_welcome_is_role_aware(self):
        status, data = self.call("GET", "/assistant/welcome", token=self.tokens["student"])
        self.assertEqual(status, 200)
        self.assertEqual(data["role"], "student")
        self.assertIn("What is the status of my enquiry?", data["suggestions"])
        self.assertFalse(data["llm_enabled"])
        status, data = self.call("GET", f"/assistant/welcome?lead_id={LEAD_ID}", token=self.tokens["manager"])
        self.assertIn("Why did this lead get its score?", data["suggestions"])

    # ------------------------------------------------------------ ML and SHAP grounding
    def test_explains_stored_prediction_without_inventing_values(self):
        status, reply = self.chat("manager", f"Explain lead {PROSPECT_ID}")
        self.assertEqual(status, 200, reply)
        self.assertEqual(reply["kind"], "lead_explain")
        card = reply["card"]
        self.assertEqual(card["lead_id"], LEAD_ID)
        self.assertEqual(card["probability"], 0.8123)          # the stored value, unchanged
        self.assertEqual(card["band"], "High")
        self.assertEqual(card["source"], "stored")
        self.assertIn("81.2%", reply["text"])
        # One-hot factor: category "Mumbai" with value "Select" means NOT Mumbai.
        self.assertIn("City is not “Mumbai” (not specified)", reply["text"])
        self.assertIn("Lead source is “Reference”", reply["text"])
        self.assertIn("Time on the website: 40 seconds", reply["text"])
        self.assertIn("not what causes", reply["text"])
        self.assertIn("not measure academic eligibility", reply["notice"])
        self.assertEqual([f["direction"] for f in card["positive"]], ["up", "up", "up"])
        self.assertEqual(card["negative"][0]["impact"], -0.72)

    def test_follow_up_uses_page_context_and_is_labelled_rule_based(self):
        status, reply = self.chat("marketing", "Suggest follow-up actions for this lead", lead_id=LEAD_ID, path=f"/student-leads/{LEAD_ID}")
        self.assertEqual(status, 200, reply)
        self.assertEqual(reply["kind"], "lead_followup")
        self.assertIn("rule-based suggestions", reply["text"])
        self.assertIn("Prioritise this lead", reply["text"])
        self.assertIn("bounced", reply["text"])                 # from the stored Last Activity factor
        self.assertIn("Pending", reply["text"])                 # from the lead record

    def test_general_question_is_not_hijacked_by_page_context(self):
        status, reply = self.chat("manager", "What is SHAP?", lead_id=LEAD_ID)
        self.assertEqual(reply["kind"], "faq")
        self.assertIsNone(reply["card"])

    def test_lead_without_stored_prediction_never_gets_a_made_up_score(self):
        status, reply = self.chat("manager", f"explain lead {NO_PREDICTION_ID}")
        self.assertEqual(status, 200, reply)
        self.assertIn(reply["kind"], ("lead_explain", "lead_missing"))
        if reply["kind"] == "lead_explain":                    # live inference from the existing endpoint
            self.assertEqual(reply["card"]["source"], "live")
            self.assertTrue(0.0 <= reply["card"]["probability"] <= 1.0)
        else:
            self.assertIsNone(reply["card"])

    def test_unknown_lead(self):
        status, reply = self.chat("manager", "explain lead 00000000-0000-4000-8000-000000000000")
        self.assertEqual(reply["kind"], "lead_not_found")

    def test_asks_which_lead_when_none_is_given(self):
        status, reply = self.chat("manager", "Why did this lead get its score?")
        self.assertEqual(reply["kind"], "clarify")

    def test_prediction_statistics_match_database(self):
        status, reply = self.chat("manager", "How many leads are in each score band?")
        self.assertEqual(reply["kind"], "stats")
        self.assertIn("1 of 2 leads have a stored prediction", reply["text"])
        self.assertIn("High: 1 (100.0%)", reply["text"])

    # ------------------------------------------------------------ role-based access
    def test_students_and_admins_cannot_see_lead_scores(self):
        for who in ("student", "admin"):
            status, reply = self.chat(who, f"Explain lead {PROSPECT_ID}")
            self.assertEqual(status, 200)
            self.assertEqual(reply["kind"], "forbidden", who)
            self.assertIsNone(reply["card"])
            self.assertNotIn("81.2", reply["text"])

    def test_student_sees_only_own_enquiries(self):
        status, reply = self.chat("student", "What is the status of my enquiry?")
        self.assertEqual(reply["kind"], "student_enquiries")
        self.assertIn("BCA: Counselling", reply["text"])
        status, reply = self.chat("other", "What is the status of my enquiry?")
        self.assertIn("haven't submitted an enquiry", reply["text"])

    # ------------------------------------------------------------ no fabrication
    def test_fees_and_admission_chance_are_not_invented(self):
        status, reply = self.chat("student", "What is the fee for MBA and the last date to apply?")
        self.assertEqual(reply["kind"], "faq")
        self.assertIn("does not store fees", reply["text"])
        self.assertFalse(any(ch.isdigit() for ch in reply["text"]))
        status, reply = self.chat("student", "What is my chance of getting admission?")
        self.assertIn("does not predict your chance of admission", reply["text"])

    def test_off_topic_questions_get_an_honest_fallback(self):
        status, reply = self.chat("student", "Who won the cricket match yesterday?")
        self.assertEqual(reply["kind"], "fallback")
        self.assertTrue(reply["suggestions"])

    # ------------------------------------------------------------ history
    def test_history_is_saved_per_user_and_can_be_cleared(self):
        token = self.tokens["other"]
        self.call("DELETE", "/assistant/history", token=token)
        self.chat("other", "hello")
        self.chat("other", "Which programmes are offered?")
        status, items = self.call("GET", "/assistant/history", token=token)
        self.assertEqual(status, 200)
        self.assertEqual([i["role"] for i in items], ["user", "assistant", "user", "assistant"])
        self.assertEqual(items[2]["text"], "Which programmes are offered?")
        status, mine = self.call("GET", "/assistant/history", token=self.tokens["admin"])
        self.assertFalse(any(i["text"] == "Which programmes are offered?" for i in mine))
        status, result = self.call("DELETE", "/assistant/history", token=token)
        self.assertEqual(result["deleted"], 4)
        self.assertEqual(self.call("GET", "/assistant/history", token=token)[1], [])

    def test_rate_limit(self):
        token = self.login("admin@assistant.test")  # fresh token, same user
        from api import assistant
        with mock.patch.object(assistant, "RATE_LIMIT", 3):
            codes = [self.call("POST", "/assistant/chat", {"message": "hello"}, token)[0] for _ in range(4)]
        self.assertEqual(codes[:3], [200, 200, 200])
        self.assertEqual(codes[3], 429)

    # ------------------------------------------------------------ existing modules untouched
    def test_existing_prediction_endpoint_still_works(self):
        status, data = self.call("GET", f"/leads/{LEAD_ID}/prediction", token=self.tokens["manager"])
        self.assertEqual(status, 200)
        self.assertEqual(data["conversion_probability"], 0.8123)


class LlmLayerTests(unittest.TestCase):
    """The optional LLM layer, with the Anthropic client replaced by a fake."""

    def setUp(self):
        from services.assistant.engine import Reply
        self.reply = Reply(text="Lead X has an estimated 81.2% chance of converting, which puts it in the High band.",
                           kind="lead_summary", notice="Scores are not admission decisions.")

    def fake_client(self, text, stop_reason="end_turn"):
        block = mock.Mock(type="text", text=text)
        response = mock.Mock(content=[block], stop_reason=stop_reason)
        client = mock.Mock()
        client.beta.messages.create.return_value = response
        return client

    def run_polish(self, client, mode="on"):
        from services.assistant import llm
        with mock.patch.dict(os.environ, {"ASSISTANT_LLM": mode}), mock.patch.object(llm, "_get_client", return_value=client):
            return llm.polish("Tell me about lead X", self.reply)

    def test_accepts_grounded_rewrite(self):
        reply = self.run_polish(self.fake_client("Lead X looks promising: about 81.2% likely to convert (High band)."))
        self.assertEqual(reply.engine, "llm")
        self.assertIn("81.2%", reply.text)

    def test_rejects_rewrite_with_invented_numbers(self):
        reply = self.run_polish(self.fake_client("Lead X is 95% likely to convert and the fee is 50,000."))
        self.assertEqual(reply.engine, "grounded")
        self.assertIn("81.2%", reply.text)

    def test_refusal_falls_back_to_grounded_text(self):
        reply = self.run_polish(self.fake_client("", stop_reason="refusal"))
        self.assertEqual(reply.engine, "grounded")

    def test_disabled_layer_is_never_called(self):
        client = self.fake_client("anything")
        reply = self.run_polish(client, mode="off")
        client.beta.messages.create.assert_not_called()
        self.assertEqual(reply.engine, "grounded")

    def test_request_shape(self):
        client = self.fake_client("Lead X: 81.2% likely to convert.")
        self.run_polish(client)
        kwargs = client.beta.messages.create.call_args.kwargs
        self.assertEqual(kwargs["model"], "claude-opus-5-5")
        self.assertEqual(kwargs["fallbacks"], "default")
        self.assertIn("server-side-fallback-2026-07-01", kwargs["betas"])
        self.assertIn("81.2%", kwargs["messages"][0]["content"])
        self.assertNotIn("temperature", kwargs)


if __name__ == "__main__":
    unittest.main()
