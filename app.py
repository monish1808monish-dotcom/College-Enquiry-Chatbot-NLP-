"""Flask web application for the fictional college FAQ chatbot."""

import logging

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import BadRequest, HTTPException, RequestEntityTooLarge

from chatbot import CollegeChatbot
from config import Config


def create_app(config_overrides=None):
    """Create the Flask application and initialize its FAQ model once."""
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)

    if not 0 <= app.config["SIMILARITY_THRESHOLD"] <= 1:
        raise ValueError("SIMILARITY_THRESHOLD must be between 0 and 1.")
    if not 0 <= app.config["AMBIGUITY_MARGIN"] <= 1:
        raise ValueError("AMBIGUITY_MARGIN must be between 0 and 1.")
    if app.config["MAX_MESSAGE_LENGTH"] < 1 or app.config["MAX_CONTENT_LENGTH"] < 1:
        raise ValueError("Message and request size limits must be positive.")

    app.config["MAX_CONTENT_LENGTH"] = app.config["MAX_CONTENT_LENGTH"]
    app.extensions["college_chatbot"] = CollegeChatbot(
        app.config["FAQ_FILE"],
        similarity_threshold=app.config["SIMILARITY_THRESHOLD"],
        ambiguity_margin=app.config["AMBIGUITY_MARGIN"],
    )

    @app.get("/")
    def home():
        college = app.extensions["college_chatbot"].college
        return render_template(
            "index.html", college_name=college.get("name", "College Enquiry Chatbot"),
            demo_notice=college.get("notice", "Demo application: College information is fictional."),
        )

    @app.post("/chat")
    def chat():
        if request.mimetype != "application/json":
            return jsonify(error="Please send this request as application/json."), 415
        try:
            payload = request.get_json(force=False, silent=False)
        except BadRequest:
            return jsonify(error="The request body must contain valid JSON."), 400
        if not isinstance(payload, dict):
            return jsonify(error="The JSON request body must be an object."), 400
        if "message" not in payload:
            return jsonify(error="The request must include a message."), 400
        message = payload["message"]
        if not isinstance(message, str):
            return jsonify(error="Message must be a string."), 400
        if not message.strip():
            return jsonify(error="Message cannot be empty."), 400
        if len(message) > app.config["MAX_MESSAGE_LENGTH"]:
            return jsonify(
                error=f"Message must be {app.config['MAX_MESSAGE_LENGTH']} characters or fewer."
            ), 400
        return jsonify(app.extensions["college_chatbot"].reply(message)), 200

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.errorhandler(RequestEntityTooLarge)
    def request_too_large(_error):
        return jsonify(error="The request is too large."), 413

    @app.errorhandler(HTTPException)
    def http_error(error):
        if isinstance(error, RequestEntityTooLarge):
            return jsonify(error="The request is too large."), 413
        return jsonify(error="The request could not be completed."), error.code

    @app.errorhandler(Exception)
    def unexpected_error(error):
        app.logger.exception("Unexpected application error")
        return jsonify(error="An unexpected server error occurred. Please try again."), 500

    return app


app = create_app()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(host="127.0.0.1", port=5000, debug=app.config["DEBUG"])