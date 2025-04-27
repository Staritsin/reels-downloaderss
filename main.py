from flask import Flask, request, jsonify, send_from_directory
import yt_dlp
import os
import tempfile
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
DOWNLOAD_PATH = "static"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

@app.route("/")
def home():
    return "✅ ReelsDownloader is live!"

@app.route("/download", methods=["GET"])
def download():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    try:
        if "youtube.com" in url or "youtu.be" in url:
            # Если это YouTube
            ydl_opts = {
                'outtmpl': f'{DOWNLOAD_PATH}/output.%(ext)s',
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
                'quiet': True,
                'noplaylist': True,
                'geo_bypass': True,
                'nocheckcertificate': True,
                'source_address': '0.0.0.0',
                'cookiefile': 'cookies.txt',
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info).replace(".webm", ".mp4").replace(".mkv", ".mp4")
                basename = os.path.basename(filename)
        else:
            # Все остальные ссылки (Instagram, TikTok)
            filename = f"{DOWNLOAD_PATH}/output.mp4"
            r = requests.get(url, allow_redirects=True)
            with open(filename, 'wb') as f:
                f.write(r.content)
            basename = "output.mp4"

        public_url = f"{request.host_url}static/{basename}"
        return jsonify({"url": public_url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/transcribe", methods=["POST"])
def transcribe():
    data = request.get_json()
    video_url = data.get("url")
    if not video_url:
        return jsonify({"error": "Missing 'url'"}), 400

    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
            r = requests.get(video_url, stream=True)
            for chunk in r.iter_content(chunk_size=8192):
                tmp_file.write(chunk)
            tmp_path = tmp_file.name

        with open(tmp_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="text"
            )

        os.remove(tmp_path)
        return jsonify({"transcription": transcript})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Обработка файлов из /static
@app.route("/static/<path:filename>")
def serve_file(filename):
    return send_from_directory(DOWNLOAD_PATH, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
