import base64
import json
import os
import re

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from openai import OpenAI

load_dotenv()

API_KEY = os.environ.get("OPENAI_API_KEY")
BASE_URL = os.environ.get("OPENAI_BASE_URL")
MODEL_NAME = os.environ.get("OPENAI_MODEL", "google/gemini-3.8-flash")
client = OpenAI(api_key=API_KEY, base_url=BASE_URL) if API_KEY else None

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200MB lecture audio

PROMPT = """You are an assistant that processes a recorded lecture audio.
Listen to the audio and respond with ONLY valid JSON (no markdown fences, no commentary) in this exact shape:
{
  "title": "short descriptive title for the lecture",
  "summary": "a clear multi-paragraph summary of the lecture content",
  "key_points": ["point 1", "point 2", "..."],
  "questions": [
    {"question": "...", "answer": "..."},
    ...
  ]
}
Generate at least 5 and at most 10 questions that test understanding of the material, each with a concise correct answer.
"""

AUDIO_FORMATS = {".mp3": "mp3", ".wav": "wav", ".m4a": "m4a", ".ogg": "ogg", ".flac": "flac"}


def extract_json(text):
    """Strip optional markdown code fences and parse JSON.

    ponytail: naive fence-stripping, not a full markdown parser. Upgrade if
    the model starts returning JSON embedded in richer prose.
    """
    cleaned = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    return json.loads(cleaned)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/process", methods=["POST"])
def process_audio():
    if not client:
        return jsonify({"error": "OPENAI_API_KEY is not set on the server (.env)"}), 500

    audio = request.files.get("audio")
    if not audio or not audio.filename:
        return jsonify({"error": "No audio file uploaded"}), 400

    suffix = os.path.splitext(audio.filename)[1].lower() or ".mp3"
    audio_format = AUDIO_FORMATS.get(suffix, "mp3")
    audio_b64 = base64.b64encode(audio.read()).decode("utf-8")

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPT},
                        {
                            "type": "input_audio",
                            "input_audio": {"data": audio_b64, "format": audio_format},
                        },
                    ],
                }
            ],
        )
        text = response.choices[0].message.content

        try:
            result = extract_json(text)
        except json.JSONDecodeError:
            result = {
                "title": "Lecture Summary",
                "summary": text,
                "key_points": [],
                "questions": [],
            }

        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
