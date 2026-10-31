"""Focused tests for FAQ retrieval and the Flask API."""

import json
import tempfile
import unittest
from pathlib import Path

from app import create_app
from chatbot import CollegeChatbot, FALLBACK_REPLY


FIXTURE = {
    "college": {"name": "Test College", "notice": "Fictional test data."},
    "faqs": [
        {
            "id": "mca_fees", "category": "Fees",
            "questions": ["What is the MCA fee?", "How much does MCA cost?", "Tell me the MCA tuition fee."],
            "answer": "The MCA fee answer.",
        },
        {
            "id": "mba_fees", "category": "Fees",
            "questions": ["What is the MBA fee?", "How much does MBA cost?", "Tell me the MBA tuition fee."],
            "answer": "The MBA fee answer.",
        },
        {
            "id": "tuition_fees", "category": "Fees",
            "questions": ["What are the tuition fees?", "Tell me about tuition fees.", "How much is tuition?"],
            "answer": "The tuition fee answer.",
        },
        {
            "id": "hostel_facilities_fees", "category": "Fees",
            "questions": ["What is the hostel fee?", "How much does hostel accommodation cost?", "Tell me about hostel fees."],
            "answer": "The hostel fee answer.",
        },
        {
            "id": "timings", "category": "Timings",
            "questions": ["What are the college timings?", "When does the college open?", "Tell me the campus working hours."],
            "answer": "The college timings answer.",
        },
        {
            "id": "scholarship", "category": "Scholarships",
            "questions": ["Are scholarships available?", "How can I apply for a scholarship?", "Does the college offer financial aid?"],
            "answer": "The scholarship answer.",
        },
    ],
}


class CollegeChatbotTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.faq_path = Path(self.temp_dir.name) / "faqs.json"
        self.faq_path.write_text(json.dumps(FIXTURE), encoding="utf-8")
        self.bot = CollegeChatbot(self.faq_path, similarity_threshold=0.30, ambiguity_margin=0.05)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_exact_question_returns_answer(self):
        self.assertEqual(self.bot.reply("What is the MCA fee?")["reply"], "The MCA fee answer.")

    def test_natural_variation_returns_answer(self):
        self.assertEqual(self.bot.reply("How much does MCA cost?")["reply"], "The MCA fee answer.")

    def test_course_fee_does_not_match_another_course(self):
        response = self.bot.reply("What is the MBA fee?")
        self.assertEqual(response["reply"], "The MBA fee answer.")

    def test_unrelated_question_falls_back(self):
        self.assertEqual(self.bot.reply("What is the weather today?")["reply"], FALLBACK_REPLY)

    def test_generic_fees_question_clarifies(self):
        response = self.bot.reply("Tell me about fees.")
        self.assertEqual(response["type"], "clarification")
        self.assertIn("Which fees", response["reply"])

    def test_greeting_returns_greeting(self):
        self.assertEqual(self.bot.reply("Hello!")["type"], "greeting")

    def test_greeting_before_question_still_retrieves_faq(self):
        response = self.bot.reply("Hello, what are the college timings?")
        self.assertEqual(response["reply"], "The college timings answer.")

    def test_scholarship_is_not_classified_as_hi(self):
        self.assertEqual(self.bot.reply("Are scholarships available?")["type"], "faq")

    def test_empty_and_non_string_messages_are_rejected(self):
        for message in ("   ", None, 12):
            with self.subTest(message=message), self.assertRaises(ValueError):
                self.bot.reply(message)


class FlaskRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.faq_path = Path(cls.temp_dir.name) / "faqs.json"
        cls.faq_path.write_text(json.dumps(FIXTURE), encoding="utf-8")
        cls.app = create_app({"TESTING": True, "FAQ_FILE": cls.faq_path})
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def test_malformed_json_is_rejected(self):
        response = self.client.post("/chat", data="{bad", content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_unsupported_content_type_is_rejected(self):
        response = self.client.post("/chat", data="message=hi", content_type="text/plain")
        self.assertEqual(response.status_code, 415)

    def test_json_object_and_message_validation(self):
        for payload in (["hi"], {}, {"message": "  "}, {"message": 5}):
            with self.subTest(payload=payload):
                response = self.client.post("/chat", json=payload)
                self.assertEqual(response.status_code, 400)

    def test_home_and_health_load(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        health = self.client.get("/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.get_json(), {"status": "ok"})


if __name__ == "__main__":
    unittest.main()