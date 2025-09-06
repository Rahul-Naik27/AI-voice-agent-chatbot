# 🎙️ AI Voice Agent – 30 Days of AI Voice Agents Challenge

📌 Overview :

This project is part of the Murf AI – **30 Days of AI Voice Agents Challenge.** It is a conversational AI Voice Agent built with Flask, Murf API, and Gemini LLM. It demonstrates how to build a conversational **AI Voice Agent** that listens, understands, and responds with a natural Murf-generated voice. The agent allows users to:

🎤 Record speech directly in the browser

📝 Transcribe speech to text using AssemblyAI

💡 Generate intelligent text replies using Google Gemini

🔊 Convert replies into lifelike speech using Murf API

🎧 Play the generated voice response in real-time

The agent combines **speech-to-text (STT)**, **large language models (LLM)**, and **text-to-speech (TTS)** into a single interactive experience.
The project creates an interactive, voice-driven chat experience directly in the browser.

## 🛠️ Tech Stack

- **Backend:** Python, Flask  
- **Frontend:** HTML, CSS, JavaScript
- **APIs:**  
  - 🎤 [AssemblyAI](https://www.assemblyai.com/) – Speech-to-Text (STT)  
  - 🧠 [Google Gemini](https://ai.google/) – LLM for conversational AI  
  - 🔊 [Murf AI](https://murf.ai/) – Text-to-Speech (TTS)  




## 🔑 Environment Variables

Create a `.env` file in the project root with:

```bash
MURF_API_KEY=your_murf_api_key
ASSEMBLYAI_API_KEY=your_assemblyai_api_key
GEMINI_API_KEY=your_gemini_api_key
```
## 🏃 Getting Started

### 1️⃣ Clone the repo

git clone https://github.com/Rahul-Naik27/AI-voice-agent-chatbot.git
cd AI-voice-agent-chatbot

### 2️⃣ Install dependencies
pip install -r requirements.txt

### 3️⃣ Run the server
python app.py
## 📦 Requirements

Create a `requirements.txt` file with the following:

```txt
Flask
Flask-Cors
python-dotenv
requests
assemblyai
google-generativeai
```
#### Explanation:
##### Flask → web server
##### Flask-Cors → handle CORS requests from frontend
##### python-dotenv → load .env with API keys
##### requests → for calling Murf API + others
##### assemblyai → SDK for transcription
##### google-generativeai → SDK for Gemini LLM
