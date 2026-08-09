# M.J. AI — Web Demo

A safe browser version of the M.J. desktop assistant for a portfolio.

## Web version includes
- Gemini-powered chat
- Conversation context
- Browser speech-to-text when supported
- Browser text-to-speech
- Futuristic M.J. interface
- Responsive design
- Server-side API key protection

## Desktop-only features
The original desktop M.J. project can control local applications, screen capture,
brightness, microphone, and other OS features. Those features are intentionally
not exposed to website visitors.

## Run locally

1. Create a Python environment.
2. Install dependencies:
   `pip install -r requirements.txt`
3. Set `GEMINI_API_KEY` in your environment.
4. Run:
   `python app.py`

## Deploy on Render

Create a free Python Web Service and use:
- Build: `pip install -r requirements.txt`
- Start: `gunicorn app:app`
- Environment variable: `GEMINI_API_KEY`

Never commit an API key to Git.
