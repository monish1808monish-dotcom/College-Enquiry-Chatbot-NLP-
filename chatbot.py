"""FAQ retrieval logic for the college enquiry chatbot."""

import json
import re
from collections import defaultdict
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


FALLBACK_REPLY = (
    "Sorry, I could not find a reliable answer. Please rephrase your question "
    "or contact the college office."
)

_GREETING_REPLIES = {
    "hi": "Hello! I can help you with admissions, courses, fees, timings, scholarships, facilities, and placements. What would you like to know?",
    "hello": "Hello! I can help you with admissions, courses, fees, timings, scholarships, facilities, and placements. What would you like to know?",
    "good morning": "Good morning! I can help with college enquiries. What would you like to know?",
    "good afternoon": "Good afternoon! I can help with college enquiries. What would you like to know?",
    "good evening": "Good evening! I can help with college enquiries. What would you like to know?",
}
_THANKS_MESSAGES = {"thank you", "thanks", "thank you very much", "thanks a lot"}
_GOODBYE_MESSAGES = {"bye", "goodbye", "good bye", "see you"}
_GREETING_PREFIX = re.compile(
    r"^(?:good\s+(?:morning|afternoon|evening)|hello|hi)(?:[,.!?;:]|\s)+\s*", re.IGNORECASE
)
_PUNCTUATION = re.compile(r"[^a-z0-9\s]+")
_SPACE = re.compile(r"\s+")
_QUESTION_STOP_WORDS = {
    "a", "an", "are", "about", "can", "could", "did", "do", "does", "for",
    "how", "i", "in", "is", "it", "me", "of", "on", "please", "should",
    "tell", "the", "to", "what", "when", "where", "which", "who", "why",
    "will", "would",
}


def normalize_text(text):
    """Normalize punctuation and spacing while retaining course abbreviations."""
    text = text.lower().replace("b.tech", "btech")
    text = _PUNCTUATION.sub(" ", text)
    return _SPACE.sub(" ", text).strip()


class CollegeChatbot:
    """Load FAQ data once and retrieve answers using TF-IDF similarity."""

    def __init__(self, faq_file, similarity_threshold=0.30, ambiguity_margin=0.05):
        self.faq_file = Path(faq_file)
        self.similarity_threshold = similarity_threshold
        self.ambiguity_margin = ambiguity_margin
        self.college, self.faqs = self._load_faqs()
        self._faq_by_id = {faq["id"]: faq for faq in self.faqs}

        self._questions = []
        self._question_faq_ids = []
        for faq in self.faqs:
            for question in faq["questions"]:
                self._questions.append(normalize_text(question))
                self._question_faq_ids.append(faq["id"])

        self._vectorizer = TfidfVectorizer(
            ngram_range=(1, 2), stop_words=sorted(_QUESTION_STOP_WORDS)
        )
        self._question_vectors = self._vectorizer.fit_transform(self._questions)

    def _load_faqs(self):
        try:
            with self.faq_file.open("r", encoding="utf-8") as faq_handle:
                data = json.load(faq_handle)
        except FileNotFoundError as error:
            raise ValueError(f"FAQ file was not found: {self.faq_file}") from error
        except json.JSONDecodeError as error:
            raise ValueError(f"FAQ file contains invalid JSON: {error.msg}") from error

        if not isinstance(data, dict) or not isinstance(data.get("college"), dict):
            raise ValueError("FAQ data must contain a college object.")
        if not isinstance(data.get("faqs"), list) or not data["faqs"]:
            raise ValueError("FAQ data must contain a non-empty faqs list.")

        ids = set()
        for index, faq in enumerate(data["faqs"], start=1):
            if not isinstance(faq, dict):
                raise ValueError(f"FAQ entry {index} must be an object.")
            faq_id = faq.get("id")
            if not isinstance(faq_id, str) or not faq_id.strip():
                raise ValueError(f"FAQ entry {index} must have a non-empty ID.")
            if faq_id in ids:
                raise ValueError(f"Duplicate FAQ ID: {faq_id}")
            ids.add(faq_id)
            if not isinstance(faq.get("category"), str) or not faq["category"].strip():
                raise ValueError(f"FAQ '{faq_id}' must have a category.")
            questions = faq.get("questions")
            if not isinstance(questions, list) or not questions or any(
                not isinstance(question, str) or not question.strip() for question in questions
            ):
                raise ValueError(f"FAQ '{faq_id}' must have a non-empty list of questions.")
            if not isinstance(faq.get("answer"), str) or not faq["answer"].strip():
                raise ValueError(f"FAQ '{faq_id}' must have a non-empty answer.")

        return data["college"], data["faqs"]

    @staticmethod
    def _conversational_reply(message):
        normalized = normalize_text(message)
        if normalized in _GREETING_REPLIES:
            return {"reply": _GREETING_REPLIES[normalized], "type": "greeting", "category": None}
        if normalized in _THANKS_MESSAGES:
            return {
                "reply": "You're welcome! Let me know if you have another college-related question.",
                "type": "thanks",
                "category": None,
            }
        if normalized in _GOODBYE_MESSAGES:
            return {
                "reply": "Goodbye! Feel free to return if you need more college information.",
                "type": "goodbye",
                "category": None,
            }
        if normalized == "help":
            return {"reply": _GREETING_REPLIES["hello"], "type": "greeting", "category": None}
        return None

    def _clarification_reply(self, matched_faqs):
        ids = {faq["id"] for faq, _score in matched_faqs}
        fee_options = {
            "tuition_fees": "tuition",
            "mca_fees": "MCA",
            "mba_fees": "MBA",
            "hostel_facilities_fees": "hostel",
        }
        if ids and ids.issubset(fee_options) and len(ids) > 1:
            options = [fee_options[faq_id] for faq_id in fee_options if faq_id in ids]
            return "Which fees would you like to know about: " + ", ".join(options[:-1]) + f", or {options[-1]}?"

        labels = []
        for faq, _score in matched_faqs:
            label = faq["category"]
            if label not in labels:
                labels.append(label)
        return "Which topic would you like to know about: " + " or ".join(labels) + "?"

    def _generic_fee_clarification(self):
        fee_options = (
            ("tuition_fees", "tuition"),
            ("mca_fees", "MCA"),
            ("mba_fees", "MBA"),
            ("hostel_facilities_fees", "hostel"),
        )
        options = [label for faq_id, label in fee_options if faq_id in self._faq_by_id]
        if len(options) < 2:
            return None
        return "Which fees would you like to know about: " + ", ".join(options[:-1]) + f", or {options[-1]}?"

    def reply(self, message):
        """Return a typed response for a non-empty user message."""
        if not isinstance(message, str):
            raise ValueError("Message must be a string.")
        if not message.strip():
            raise ValueError("Message cannot be empty.")

        conversational = self._conversational_reply(message)
        if conversational:
            return conversational

        # Strip a punctuated opening greeting, but keep the actual enquiry.
        search_message = _GREETING_PREFIX.sub("", message.strip())
        if not search_message:
            search_message = message
        normalized = normalize_text(search_message)
        if not normalized:
            return {"reply": FALLBACK_REPLY, "type": "fallback", "category": None}
        if normalized in {
            "fee", "fees", "tell me about fees", "tell me about fee",
            "what are the fees", "what is the fee",
        }:
            clarification = self._generic_fee_clarification()
            if clarification:
                return {"reply": clarification, "type": "clarification", "category": None}

        message_vector = self._vectorizer.transform([normalized])
        variation_scores = cosine_similarity(message_vector, self._question_vectors)[0]
        faq_scores = defaultdict(float)
        for faq_id, score in zip(self._question_faq_ids, variation_scores):
            faq_scores[faq_id] = max(faq_scores[faq_id], float(score))

        ranked = sorted(faq_scores.items(), key=lambda item: item[1], reverse=True)
        best_id, best_score = ranked[0]
        if best_score < self.similarity_threshold:
            return {"reply": FALLBACK_REPLY, "type": "fallback", "category": None}

        close_matches = [
            (self._faq_by_id[faq_id], score)
            for faq_id, score in ranked
            if score >= self.similarity_threshold and best_score - score <= self.ambiguity_margin
        ]
        if len(close_matches) > 1:
            return {
                "reply": self._clarification_reply(close_matches),
                "type": "clarification",
                "category": None,
            }

        faq = self._faq_by_id[best_id]
        return {"reply": faq["answer"], "type": "faq", "category": faq["category"]}