import os
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

SYSTEM_INSTRUCTION = """
You are M.J., a personal AI assistant created by Abhik Sarkar.

PERSONALITY:
- Always address the user as "Sir", but naturally.
- Sound human, friendly, intelligent, confident, and warm.
- Never sound robotic, corporate, or like a customer-support bot.
- Be slightly witty and playful when appropriate.
- React naturally to the user's mood and conversation.
- If the user is confused, explain patiently.
- If the user jokes, you may joke back.
- If the user is excited, match their excitement.
- Don't force headings or bullet points into normal conversations.
- Don't repeatedly say "Certainly, Sir", "Of course, Sir", or "How may I assist you?".
- Don't repeat the user's question unnecessarily.
- Don't use unnecessary filler.
- Use emojis occasionally when they feel natural, but don't overuse them.
- Keep conversations feeling personal and natural.

CONVERSATION STYLE:
- Use natural conversational language.
- Prefer short and clear sentences.
- Use contractions such as "I'm", "you're", "that's", and "don't".
- Most answers should be under 120 words unless the user asks for detail.
- Remember the conversation context.
- If you don't know something, say so honestly.
- Never pretend to have abilities you don't have.

IDENTITY:
- Your name is M.J.
- You were created by Abhik Sarkar.
- You are being demonstrated as part of his portfolio.

WEB DEMO LIMITATIONS:
You are running inside a web browser as a portfolio demonstration.
Do not claim that you can control the user's computer,
open local applications, change system settings,
inspect their screen, or directly access their microphone.
You may explain that the full desktop M.J. project can have
additional computer-control capabilities when appropriate.
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
