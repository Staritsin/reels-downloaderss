from flask import Flask, request, send_file, jsonify
import yt_dlp
import os
import tempfile
import requests
import openai
from dotenv import load_dotenv


app = Flask(__name__)
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


DOWNLOAD_PATH = "downloads"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

@app.route("/")
def home():
    return "Reels Downloader API is working!"

@app.route("/download", methods=["GET"])
def download():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing URL parameter"}), 400

    try:
        ydl_opts = {
            'outtmpl': f'{DOWNLOAD_PATH}/output.%(ext)s',
            'format': 'mp4',
            'quiet': True,
            'noplaylist': True,
            'merge_output_format': 'mp4'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info).replace(".webm", ".mp4").replace(".mkv", ".mp4")

        return send_file(filename, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/transcribe", methods=["POST"])
def transcribe():
    data = request.get_json()
    video_url = data.get("url")

    if not video_url:
        return jsonify({"error": "Missing 'url' in request body"}), 400

    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
            r = requests.get(video_url, stream=True)
            for chunk in r.iter_content(chunk_size=8192):
                tmp_file.write(chunk)
            tmp_path = tmp_file.name

        with open(tmp_path, "rb") as f:
            transcript = openai.Audio.transcribe("whisper-1", f)

        os.remove(tmp_path)
        return jsonify({"transcription": transcript["text"]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
