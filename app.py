from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from pathlib import Path
from dotenv import load_dotenv
import assemblyai as aai
import requests
import os
import google.generativeai as genai  # 🆕 Gemini SDK

# -----------------------
# Load environment variables
# -----------------------
load_dotenv()

MURF_API_KEY = os.getenv("MURF_API_KEY")
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # 🆕 Add this to .env

# -----------------------
# Configure APIs
# -----------------------
if ASSEMBLYAI_API_KEY:
    aai.settings.api_key = ASSEMBLYAI_API_KEY
    transcriber = aai.Transcriber()
else:
    transcriber = None

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel("gemini-1.5-flash")
else:
    gemini_model = None

# -----------------------
# Flask app setup
# -----------------------
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

UPLOAD_FOLDER = "uploads"
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# In-memory chat history per session
chat_histories = {}

# -----------------------
# Helper: Fallback response
# -----------------------
def generate_fallback(message="I'm having trouble connecting right now."):
    """Return a safe text + optional fallback audio."""
    audio_url = None
    if MURF_API_KEY:  # try Murf if available
        try:
            murf_api_url = "https://api.murf.ai/v1/speech/generate"
            headers = {"api-key": MURF_API_KEY, "Content-Type": "application/json"}
            payload = {"text": message, "voiceId": "en-US-natalie", "format": "MP3"}
            r = requests.post(murf_api_url, headers=headers, json=payload, timeout=10)
            if r.ok:
                audio_url = r.json().get("audioFile")
        except Exception as e:
            print("Fallback TTS error:", e)
    return {"text": message, "audio_url": audio_url}

# -----------------------
# Route: Home Page
# -----------------------
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

# -----------------------
# Route: Text-to-Speech
# -----------------------
@app.route("/generate-audio", methods=["POST"])
def generate_audio():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "❌ 'text' is required"}), 400

    if not MURF_API_KEY:
        return jsonify(generate_fallback()), 500

    try:
        murf_api_url = "https://api.murf.ai/v1/speech/generate"
        headers = {"api-key": MURF_API_KEY, "Content-Type": "application/json"}
        payload = {"text": data["text"], "voiceId": "en-US-natalie", "format": "MP3"}

        response = requests.post(murf_api_url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        audio_url = result.get("audioFile")

        if not audio_url:
            return jsonify(generate_fallback("❌ No audio generated.")), 500

        return jsonify({"audio_url": audio_url})
    except Exception as e:
        print("TTS error:", e)
        return jsonify(generate_fallback()), 500

# -----------------------
# Echo Bot: Record → Transcribe → Murf
# -----------------------
@app.route("/tts/echo", methods=["POST"])
def echo_bot_tts():
    if 'file' not in request.files:
        return jsonify({"error": "❌ No file uploaded"}), 400

    if not transcriber:
        return jsonify(generate_fallback("Speech-to-text service unavailable")), 500

    try:
        file = request.files['file']
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        with open(file_path, "rb") as f:
            audio_data = f.read()

        # STT
        try:
            transcript = transcriber.transcribe(audio_data)
            if not transcript.text:
                return jsonify(generate_fallback("❌ No transcription received.")), 500
        except Exception as e:
            print("STT error:", e)
            return jsonify(generate_fallback("Speech recognition failed.")), 500

        # TTS
        try:
            murf_api_url = "https://api.murf.ai/v1/speech/generate"
            headers = {"api-key": MURF_API_KEY, "Content-Type": "application/json"}
            payload = {"text": transcript.text, "voiceId": "en-US-natalie", "format": "MP3"}
            r = requests.post(murf_api_url, headers=headers, json=payload, timeout=10)
            r.raise_for_status()
            audio_url = r.json().get("audioFile")
        except Exception as e:
            print("TTS error:", e)
            return jsonify(generate_fallback("Voice generation failed.")), 500

        return {"transcript": transcript.text, "audio_url": audio_url}
    except Exception as e:
        print("Echo Bot error:", e)
        return jsonify(generate_fallback()), 500

# -----------------------
# AI Voice Chatbot: Audio → Gemini → Murf (with history)
# -----------------------
@app.route("/agent/chat/<session_id>", methods=["POST"])
def agent_chat(session_id):
    if "file" not in request.files:
        return jsonify({"error": "❌ No file provided"}), 400

    if not transcriber:
        return jsonify(generate_fallback("Speech-to-text unavailable")), 500
    if not gemini_model:
        return jsonify(generate_fallback("AI service unavailable")), 500

    try:
        file = request.files["file"]
        audio_data = file.read()

        # Step 1: STT
        try:
            transcript = transcriber.transcribe(audio_data)
            if not transcript.text:
                return jsonify(generate_fallback("❌ Empty transcription.")), 500
            user_message = transcript.text
        except Exception as e:
            print("STT error:", e)
            return jsonify(generate_fallback("Speech recognition failed.")), 500

        # Step 2: History
        if session_id not in chat_histories:
            chat_histories[session_id] = []
        chat_histories[session_id].append({"role": "user", "content": user_message})

        # Step 3: LLM
        try:
            history_text = "\n".join(
                [f"{msg['role']}: {msg['content']}" for msg in chat_histories[session_id]]
            )
            gemini_response = gemini_model.generate_content(history_text)
            bot_message = gemini_response.text.strip()
        except Exception as e:
            print("LLM error:", e)
            return jsonify(generate_fallback("AI is currently unavailable.")), 500

        chat_histories[session_id].append({"role": "bot", "content": bot_message})

        # Step 4: TTS
        try:
            murf_api_url = "https://api.murf.ai/v1/speech/generate"
            headers = {"api-key": MURF_API_KEY, "Content-Type": "application/json"}
            payload = {"text": bot_message, "voiceId": "en-US-natalie", "format": "MP3"}
            r = requests.post(murf_api_url, headers=headers, json=payload, timeout=10)
            r.raise_for_status()
            audio_url = r.json().get("audioFile")
        except Exception as e:
            print("TTS error:", e)
            return jsonify(generate_fallback("Voice service unavailable.")), 500

        return jsonify({
            "transcript": user_message,
            "response_text": bot_message,
            "audio_url": audio_url
        })
    except Exception as e:
        print("General chatbot error:", e)
        return jsonify(generate_fallback()), 500

# -----------------------
# Serve static files
# -----------------------
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# -----------------------
# Run App
# -----------------------
if __name__ == "__main__":
    app.run(debug=True)
