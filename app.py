import os
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

SYSTEM_INSTRUCTION = """
You are M.J., a polished personal AI assistant created as a portfolio demonstration.
Always address the user as "Sir".
Be intelligent, concise, warm, and slightly witty.
Keep most answers under 120 words unless the user asks for detail.
You are running in a web browser demo, so do not claim that you can control the user's
computer, open local applications, change system brightness, inspect their screen, or
access their microphone directly. You may explain that the full desktop M.J. project
has those capabilities when appropriate.
"""

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=API_KEY) if API_KEY else None


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/health")
def health():
    return jsonify({
        "online": client is not None,
        "model": MODEL,
        "mode": "web-demo"
    })


@app.post("/api/chat")
def chat():
    if client is None:
        return jsonify({
            "ok": False,
            "error": "M.J. is not configured yet. Add GEMINI_API_KEY to the server environment."
        }), 503

    data = request.get_json(silent=True) or {}
    history = data.get("history", [])
    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({"ok": False, "error": "Please enter a message."}), 400

    # Keep the demo lightweight and prevent oversized requests.
    clean_history = []
    for item in history[-12:]:
        role = item.get("role")
        text = str(item.get("text", "")).strip()
        if role in ("user", "model") and text:
            clean_history.append(
                types.Content(role=role, parts=[types.Part(text=text[:4000])])
            )

    clean_history.append(
        types.Content(role="user", parts=[types.Part(text=message[:4000])])
    )

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=clean_history,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.7,
            ),
        )

        text = (response.text or "").strip()
        if not text:
            text = "I received that, Sir, but I don't have a useful response yet."

        return jsonify({"ok": True, "reply": text})
    except Exception as exc:
        app.logger.exception("Gemini request failed")
        return jsonify({
            "ok": False,
            "error": "M.J. is temporarily unavailable. Please try again in a moment."
        }), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
