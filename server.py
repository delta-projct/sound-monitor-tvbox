from flask import Flask, jsonify, render_template_string
import sounddevice as sd
import numpy as np
import webrtcvad

app = Flask(__name__)

SAMPLE_RATE = 48000
DURATION = 0.48

REFERENCE_DB = 94.0
REFERENCE_RMS = 0.707

DEVICE = 0

# WebRTC VAD
vad = webrtcvad.Vad()
vad.set_mode(2)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Monitoring Suara</title>

    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>
        body {
            background: #111;
            color: white;
            text-align: center;
            font-family: Arial;
            padding-top: 50px;
        }

        h1 {
            font-size: 28px;
        }

        #db {
            font-size: 60px;
            font-weight: bold;
            margin: 30px;
        }

        #status {
            font-size: 28px;
            font-weight: bold;
            padding: 15px;
            border-radius: 10px;
            display: none;
        }

        .aman {
            background: green;
        }

        .peringatan {
            background: orange;
        }

        .bising {
            background: red;
        }

        #suaraManusia {
            font-size: 22px;
            font-weight: bold;
            margin-top: 15px;
            display: none;
        }
    </style>
</head>

<body>

    <h1>MONITORING SUARA</h1>

    <div id="db">0.00 dB</div>

    <div id="status"></div>

    <div id="suaraManusia">
        🗣️ SUARA MANUSIA
    </div>

    <script>

        function updateData() {

            fetch('/data')
            .then(response => response.json())
            .then(data => {

                document.getElementById("db").innerText =
                    data.db.toFixed(2) + " dB";

                let statusElement =
                    document.getElementById("status");

                let suaraElement =
                    document.getElementById("suaraManusia");

                if (data.human_voice) {

                    statusElement.style.display = "inline-block";
                    suaraElement.style.display = "block";

                    statusElement.innerText =
                        data.status;

                    statusElement.className = "";

                    if (data.status === "AMAN") {

                        statusElement.classList.add("aman");

                    } else if (data.status === "PERINGATAN") {

                        statusElement.classList.add("peringatan");

                    } else {

                        statusElement.classList.add("bising");
                    }

                } else {

                    statusElement.style.display = "none";
                    suaraElement.style.display = "none";
                }

            });
        }

        setInterval(updateData, 1000);

        updateData();

    </script>

</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/data")
def data():

    try:
        # PERUBAHAN 1: Ubah channels menjadi 2 agar didukung oleh mikrofon Rexus
        audio = sd.rec(
            int(DURATION * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=2,
            dtype="float32",
            device=DEVICE
        )

        sd.wait()

        # PERUBAHAN 2: Gabungkan suara dari 2 channel (Stereo) menjadi 1 channel (Mono)
        samples = np.mean(audio, axis=1)

        # =========================
        # HITUNG dB
        # =========================

        rms = np.sqrt(np.mean(samples ** 2))

        if rms <= 0:
            db = 0
        else:
            db = REFERENCE_DB + 20 * np.log10(
                rms / REFERENCE_RMS
            )

        # =========================
        # DETEKSI SUARA MANUSIA
        # =========================

        # Ubah float32 menjadi PCM 16-bit
        pcm = np.clip(samples * 32767, -32768, 32767).astype(np.int16)

        frame_size = int(SAMPLE_RATE * 0.03)

        speech_frames = 0
        total_frames = 0

        for start in range(0, len(pcm) - frame_size + 1, frame_size):

            frame = pcm[start:start + frame_size]

            if vad.is_speech(frame.tobytes(), SAMPLE_RATE):
                speech_frames += 1

            total_frames += 1

        # Minimal 30% frame dianggap suara manusia
        human_voice = (
            total_frames > 0 and
            speech_frames / total_frames >= 0.30
        )

        # =========================
        # STATUS KEBISINGAN
        # =========================

        if db < 50:
            status = "AMAN"

        elif db < 60:
            status = "PERINGATAN"

        else:
            status = "SANGAT BISING"

        return jsonify({
            "db": float(db),
            "status": status,
            "human_voice": human_voice
        })

    except Exception as e:

        return jsonify({
            "db": 0,
            "status": "ERROR",
            "human_voice": False,
            "error": str(e)
        })


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
