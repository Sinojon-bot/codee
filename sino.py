
from flask import Flask, jsonify, render_template_string
import cv2
import requests
import threading
from datetime import datetime
from pathlib import Path

# Telegram
BOT_TOKEN = "8967170786:AAFneP3md1WHMQoMT8CAEIJ_rEcdkL_BBcE"
CHAT_ID = "7826286091"

app = Flask(__name__)

SAVE_DIR = Path(__file__).parent / "photos"
SAVE_DIR.mkdir(exist_ok=True)

camera_lock = threading.Lock()

HTML = """
<!DOCTYPE html>
<html lang="tg">
<head>
<meta charset="UTF-8">
<meta name="viewport"
      content="width=device-width, initial-scale=1">
<title>Welcome</title>
<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    background: #0f172a;
    font-family: Arial, sans-serif;
    color: white;
    min-height: 100vh;
    display: grid;
    place-items: center;
}
.card {
    background: #1e293b;
    padding: 35px;
    border-radius: 20px;
    text-align: center;
    width: 90%;
    max-width: 420px;
}
h1 { font-size: 28px; }

p {
    color: #cbd5e1;
    line-height: 1.6;
}
button {
    background: #2563eb;
    color: white;
    border: 0;
    border-radius: 10px;
    padding: 16px 38px;
    font-size: 18px;
    cursor: pointer;
    margin-top: 15px;
}
button:disabled { opacity: .5; }

#status {
    margin-top: 20px;
    overflow-wrap: anywhere;
}
</style>
</head>
<body>

<div class="card">
    <h1>Хуш омадед!</h1>

    <p>
      Ин барномаи санҷишӣ аз камераи
      ҳамин компютер акс мегирад ва
      онро ба Telegram мефиристад.
      Бо пахши тугма шумо ба ин
      амал розигӣ медиҳед.
    </p>

    <button id="btn" onclick="start()">
        Продолжить
    </button>

    <p id="status"></p>
</div>

<script>
async function start() {
    const btn = document.getElementById("btn");
    const status = document.getElementById("status");

    btn.disabled = true;
    status.textContent = "Коркард оғоз шуд...";

    try {
        const response = await fetch("/capture", {
            method: "POST"
        });

        const result = await response.json();
        status.textContent = result.message;

    } catch (error) {
        status.textContent = "Хатои пайвастшавӣ.";
    }

    btn.disabled = false;
}
</script>

</body>
</html>
"""

@app.get("/")
def home():
    return render_template_string(HTML)


@app.post("/capture")
def capture():

    if not camera_lock.acquire(blocking=False):
        return jsonify(
            message="Камера аллакай истифода мешавад."
        ), 409

    try:
        if BOT_TOKEN == "TOKEN_HERE" or CHAT_ID == "CHAT_ID_HERE":
            return jsonify(
                message="BOT_TOKEN ва CHAT_ID-ро пур кунед."
            ), 400

        camera = cv2.VideoCapture(0)

        try:
            if not camera.isOpened():
                return jsonify(
                    message="Камера дастрас нест."
                ), 500

            success, frame = camera.read()

            if not success:
                return jsonify(
                    message="Акс гирифта нашуд."
                ), 500

        finally:
            camera.release()

        filename = datetime.now().strftime(
            "photo_%Y%m%d_%H%M%S_%f.jpg"
        )
        filepath = SAVE_DIR / filename

        if not cv2.imwrite(str(filepath), frame):
            return jsonify(
                message="Акс сабт нашуд."
            ), 500

        url = (
            f"https://api.telegram.org/"
            f"bot{BOT_TOKEN}/sendPhoto"
        )

        with open(filepath, "rb") as photo:
            response = requests.post(
                url,
                data={
                    "chat_id": CHAT_ID,
                    "caption": "Local camera test"
                },
                files={"photo": photo},
                timeout=30
            )

        response.raise_for_status()
        telegram_result = response.json()

        if not telegram_result.get("ok"):
            return jsonify(
                message="Telegram аксро қабул накард."
            ), 502

        return jsonify(
            message="Акс ба Telegram фиристода шуд."
        )

    except requests.RequestException:
        return jsonify(
            message="Хатои пайвастшавӣ ба Telegram."
        ), 502

    finally:
        camera_lock.release()


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
