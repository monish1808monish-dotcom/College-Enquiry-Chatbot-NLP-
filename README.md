# College Enquiry Chatbot Using Natural Language Processing

## Overview

This beginner-friendly web project answers common student and parent enquiries using a retrieval-based FAQ chatbot. It compares a message with questions stored in `data/faqs.json` using TF-IDF vectors and cosine similarity. It does not generate answers or retrieve information from outside the configured FAQ data.

## Problem Statement

Students and parents often repeat questions about admissions, courses, fees, facilities, and college schedules. A small chatbot can provide quick access to configured FAQ information through a simple web interface.

## Objectives

- Automate common enquiries with configured answers.
- Provide a simple, accessible web interface.
- Retrieve relevant answers using standard NLP techniques.
- Keep college information maintainable in JSON rather than Python code.

## Features

- TF-IDF and cosine-similarity retrieval with a configurable match threshold.
- FAQ validation, fallback responses, and clarification when separate topics match closely.
- Friendly greeting, thanks, goodbye, and help responses.
- Flask JSON API, request validation, a health endpoint, and focused `unittest` tests.
- Responsive chat interface with suggested questions, timestamps, a typing indicator, and in-memory-only conversation history.
- 46 fictional FAQ entries. No API key, database, external service, or downloaded language model is used.

## Technology Stack

Python, Flask, scikit-learn, JSON, HTML5, CSS3, vanilla JavaScript, and Python's standard `unittest` module.

## Project Structure

```text
college-enquiry-chatbot/
|-- app.py
|-- chatbot.py
|-- config.py
|-- data/
|   `-- faqs.json
|-- templates/
|   `-- index.html
|-- static/
|   |-- css/style.css
|   `-- js/script.js
|-- tests/
|   `-- test_chatbot.py
|-- requirements.txt
|-- .gitignore
`-- README.md
```

## Prerequisites

- Python 3.10 or later is recommended; use a Python version supported by the installed Flask and scikit-learn releases.
- VS Code and a modern web browser.
- Internet access is needed only to install the dependencies. Once installed, the application runs locally without internet access.

## Windows PowerShell Setup

Run these commands from the project folder (the folder containing `app.py`):

```powershell
py --version
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser. The Flask development server is for local development only; do not use it as a production server.

If PowerShell blocks virtual-environment activation, these commands do not require changing the execution policy:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Debug mode is off by default. To explicitly enable Flask debug mode for local development, set `$env:FLASK_DEBUG = "1"` before starting the app. Do not enable debug mode in a deployed environment.

## How the NLP Pipeline Works

1. `CollegeChatbot` loads and validates the JSON file when the Flask application is created.
2. Text is lowercased, common punctuation is normalized, and repeated whitespace is collapsed. Useful abbreviations such as MCA and MBA are preserved.
3. Every stored question variation is transformed into a TF-IDF vector once during initialization.
4. A new message is transformed with the same fitted vectorizer. Cosine similarity compares it with the stored question vectors.
5. The highest score for each FAQ is used, so repeated variations in one FAQ do not count as multiple competing topics.
6. A result below the configured threshold uses a fallback. If distinct FAQs have sufficiently close scores, the bot asks the user to clarify.

Cosine similarity scores are not probabilities. The default threshold is an initial setting, and matching may need adjustment to suit verified FAQ wording.

## Updating College Information

Edit `data/faqs.json`; the `college` object contains the college name, demo flag, notice, email, phone, and address. Each FAQ has a unique `id`, a `category`, at least three question variations, and an answer. Update an answer or add natural question variations within that object. To add a new FAQ, copy an entry and give it a unique ID. Duplicate IDs are rejected when the application starts.

This project intentionally contains fictional sample data. Replace the sample profile and every answer with information verified by the college before real use. Dates, fees, eligibility, refund rules, placement information, and bus routes should be confirmed with the college office. Restart the application after editing the JSON because FAQ data is loaded at startup. Keep the file valid JSON: use double quotes for strings, escape embedded double quotes, and do not add trailing commas. A JSON-aware editor can help validate it.

## Configuration

Settings can be supplied as environment variables before startup. Defaults are declared in `config.py`.

| Environment variable | Default | Purpose |
| --- | --- | --- |
| `FAQ_FILE` | `data/faqs.json` beside the Python files | FAQ JSON path; relative paths are resolved from the project folder. |
| `CHATBOT_SIMILARITY_THRESHOLD` | `0.30` | Minimum cosine similarity for a match; range 0 through 1. |
| `CHATBOT_AMBIGUITY_MARGIN` | `0.05` | Score difference within which separate FAQs trigger clarification; range 0 through 1. |
| `CHATBOT_MAX_MESSAGE_LENGTH` | `500` | Maximum message characters accepted by `/chat`. |
| `CHATBOT_MAX_CONTENT_LENGTH` | `16384` | Maximum HTTP request body size in bytes. |
| `FLASK_DEBUG` | off | Set to `1`, `true`, or `yes` to explicitly enable local debug mode. |

Invalid numeric settings or out-of-range values stop startup with a clear configuration error.

## API

`POST /chat` accepts JSON with a non-empty string message of up to the configured limit:

```json
{"message": "What courses are available?"}
```

Successful retrieval returns a response in this shape:

```json
{"reply": "Undergraduate course information has not been verified in this demo. Please contact the college office for the current course list.", "type": "faq", "category": "Courses"}
```

Other response types include `greeting`, `clarification`, `fallback`, `thanks`, and `goodbye`. Category is `null` where there is no single FAQ category. Invalid input returns a JSON `error` with status 400, unsupported content types return 415, oversized bodies return 413, and unexpected errors return a generic 500 message without a traceback.

`GET /health` returns a minimal status and does not expose paths or configuration:

```json
{"status": "ok"}
```

The API is same-origin; CORS is not enabled.

## Testing

From the project folder, run:

```powershell
python -m unittest discover -s tests -v
```

The tests use a deterministic temporary FAQ fixture and Flask's test client to check matching, ambiguity, greeting behavior, invalid input, JSON routes, the home page, and health response.

## Example Conversations

```text
You: Hello, what are the college timings?
Bot: The configured answer about college working hours.

You: What is the MCA fee?
Bot: MCA fees are not configured in this demo. Please contact the college office for the current verified fee schedule.

You: Tell me about fees.
Bot: Which fees would you like to know about: tuition, MCA, MBA, or hostel?

You: What is the weather today?
Bot: Sorry, I could not find a reliable answer. Please rephrase your question or contact the college office.
```

## Limitations

- The chatbot can answer only questions represented by the configured FAQs; it does not generate answers or retrieve external information.
- Text similarity can be imperfect, and a similarity score is not a probability or guarantee.
- All supplied college information is fictional and must be replaced with verified information before real use.
- The application cannot access live admission status.
- Conversation history stays in browser memory and is not saved in local storage or on the server.

## Troubleshooting

- **Python is not recognized:** Install Python, ensure it is available in `PATH`, then open a new PowerShell window. The `py --version` check helps confirm the launcher.
- **Flask or scikit-learn is missing:** Activate `.venv` and run `python -m pip install -r requirements.txt` with the same interpreter used to start the app.
- **VS Code uses the wrong interpreter:** Open the Command Palette, select **Python: Select Interpreter**, and choose `.venv`.
- **PowerShell activation is blocked:** Use the direct `.\.venv\Scripts\python.exe` commands in the setup section; no policy change is needed.
- **Port 5000 is already in use:** Stop the other local process, or start with `python -m flask --app app run --host 127.0.0.1 --port 5001` and open `http://127.0.0.1:5001`.
- **FAQ JSON is invalid:** Check commas, double quotes, and brackets with a JSON-aware editor. Startup reports the relevant validation problem.
- **The browser cannot connect:** Confirm the server is running and open the matching local URL. Check the terminal for startup errors.
- **A question returns an unrelated answer:** Rephrase it using terms present in the FAQ, verify the FAQ's question variations, and adjust the threshold cautiously. Keep unrelated questions on the fallback path.

## Future Enhancement Ideas (Not Implemented)

- Verified college data management.
- Multilingual support.
- Voice input.
- Integration with official admission systems.
- Improved semantic retrieval.
