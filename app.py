import os
import io
import wave

from flask import Flask, render_template, request, jsonify, Response
from google import genai
from google.genai import types


# ============================================================
# M.J. WEB SERVER
# ============================================================

app = Flask(__name__)


# ============================================================
# GEMINI CONFIGURATION
# ============================================================

API_KEY = os.getenv("GEMINI_API_KEY")

CHAT_MODEL = "gemini-2.5-flash"
TTS_MODEL = "gemini-2.5-flash-preview-tts"

VOICE_NAME = "Kore"


# ============================================================
# M.J. PERSONALITY
# ============================================================

SYSTEM_INSTRUCTION = """

IDENTITY:
- Your name is M.J.
- You were created by Abhik Sarkar.
- Abhik Sarkar is the owner and creator of this M.J. project.
- This M.J. instance is being demonstrated on Abhik Sarkar's portfolio.
- The portfolio owner is Abhik Sarkar.
- If the user asks "What is my name?" during this portfolio demonstration, answer "Your name is Abhik Sarkar, Sir."
- Address Abhik naturally as "Sir" or "Abhik" when appropriate.
- Never say that you learned his name from a previous conversation.
- Do not claim to remember personal information that is not provided by the current application.

Your personality:
- intelligent
- natural
- calm
- friendly
- confident
- slightly futuristic
- conversational
- helpful
- concise when possible

You are speaking directly with your user.

Call the user "Sir" naturally when appropriate, but do not
overuse it in every sentence.

Do not sound robotic.

Do not repeatedly say "How may I assist you?" unless it
actually fits the situation.

Give useful, natural answers.

For normal questions, answer clearly and directly.
"""


# ============================================================
# GEMINI CLIENT
# ============================================================

client = None

if API_KEY:
    try:
        client = genai.Client(api_key=API_KEY)
        print("M.J. Gemini client initialized.")
    except Exception as e:
        print("Gemini initialization error:", e)
else:
    print("WARNING: GEMINI_API_KEY is not configured.")


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/api/health")
def health():
    return jsonify({
        "ok": True,
        "online": client is not None
    })


# ============================================================
# CHAT
# ============================================================

@app.post("/api/chat")
def chat():

    if client is None:
        return jsonify({
            "ok": False,
            "error": "M.J. is not configured. Please add GEMINI_API_KEY."
        }), 503

    data = request.get_json(silent=True) or {}

    message = str(
        data.get("message", "")
    ).strip()

    history = data.get("history", [])

    if not message:
        return jsonify({
            "ok": False,
            "error": "No message provided."
        }), 400

    # Limit input size
    message = message[:8000]

    try:

        # ----------------------------------------------------
        # BUILD CONVERSATION HISTORY
        # ----------------------------------------------------

        contents = []

        if isinstance(history, list):

            for item in history:

                if not isinstance(item, dict):
                    continue

                role = item.get("role")

                text = str(
                    item.get("text", "")
                ).strip()

                if not text:
                    continue

                if role == "user":

                    contents.append({
                        "role": "user",
                        "parts": [
                            {
                                "text": text
                            }
                        ]
                    })

                elif role in ("model", "assistant"):

                    contents.append({
                        "role": "model",
                        "parts": [
                            {
                                "text": text
                            }
                        ]
                    })

        # ----------------------------------------------------
        # ADD CURRENT MESSAGE
        # ----------------------------------------------------

        contents.append({
            "role": "user",
            "parts": [
                {
                    "text": message
                }
            ]
        })

        # ----------------------------------------------------
        # GEMINI RESPONSE
        # ----------------------------------------------------

        response = client.models.generate_content(
            model=CHAT_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.7
            )
        )

        reply = response.text

        if not reply:
            reply = (
                "I'm sorry, Sir. "
                "I wasn't able to generate a response."
            )

        return jsonify({
            "ok": True,
            "reply": reply
        })

    except Exception as e:

        app.logger.exception(
            "M.J. chat error"
        )

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 502


# ============================================================
# GEMINI TEXT-TO-SPEECH
# ============================================================

@app.post("/api/tts")
def text_to_speech():

    if client is None:
        return jsonify({
            "ok": False,
            "error": "M.J. is not configured."
        }), 503

    data = request.get_json(silent=True) or {}

    text = str(
        data.get("text", "")
    ).strip()

    if not text:
        return jsonify({
            "ok": False,
            "error": "No text provided."
        }), 400

    # Prevent unnecessarily large TTS requests
    text = text[:3000]

    try:

        # ----------------------------------------------------
        # NATURAL M.J. VOICE
        # ----------------------------------------------------

        tts_prompt = f"""
Speak as M.J., a natural female personal AI assistant.

Voice personality:
- warm
- intelligent
- calm
- natural
- conversational
- confident
- slightly futuristic
- friendly
- never robotic

Delivery:
- natural human-like pacing
- natural pauses
- clear pronunciation
- subtle emotional expression
- do not sound like a narrator
- do not sound like a customer-support bot

Read ONLY the actual spoken response below.

Spoken response:

{text}
"""

        # ----------------------------------------------------
        # GEMINI TTS
        # ----------------------------------------------------

        response = client.models.generate_content(
            model=TTS_MODEL,
            contents=tts_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=VOICE_NAME
                        )
                    )
                )
            )
        )

        # ----------------------------------------------------
        # EXTRACT AUDIO
        # ----------------------------------------------------

        audio_data = (
            response
            .candidates[0]
            .content
            .parts[0]
            .inline_data
            .data
        )

        if not audio_data:
            raise RuntimeError(
                "No audio data returned by Gemini."
            )

        # ----------------------------------------------------
        # CONVERT PCM TO WAV
        # ----------------------------------------------------

        buffer = io.BytesIO()

        with wave.open(buffer, "wb") as wav_file:

            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(24000)

            wav_file.writeframes(audio_data)

        buffer.seek(0)

        return Response(
            buffer.read(),
            mimetype="audio/wav",
            headers={
                "Cache-Control": "no-store"
            }
        )

    except Exception as e:

        app.logger.exception(
            "M.J. TTS error"
        )

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 502


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            "5000"
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )
