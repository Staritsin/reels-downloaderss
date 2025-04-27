from flask import Flask, request, jsonify, send_file
import requests
import os
import yt_dlp
import tempfile

app = Flask(__name__)
DOWNLOAD_PATH = "static"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

@app.route("/")
def home():
    return "✅ ReelsDownloader is live!"

# Скачать по прямой ссылке
@app.route("/download-file", methods=["POST"])
def download_file():
    url = request.json.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    try:
        # Скачиваем файл
        filename = os.path.join(DOWNLOAD_PATH, "downloaded.mp4")
        r = requests.get(url, allow_redirects=True)
        open(filename, 'wb').write(r.content)

        # Отдаем файл
        return send_file(filename, mimetype="video/mp4")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Скачать через yt_dlp (например для Reels)
@app.route("/download-video", methods=["GET"])
def download_video():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    try:
        ydl_opts = {
            'outtmpl': f'{DOWNLOAD_PATH}/output.%(ext)s',
            'format': 'mp4',
            'quiet': True,
            'noplaylist': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info).replace(".webm", ".mp4").replace(".mkv", ".mp4")
            basename = os.path.basename(filename)

        public_url = f"{request.host_url}static/{basename}"
        return jsonify({"url": public_url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
