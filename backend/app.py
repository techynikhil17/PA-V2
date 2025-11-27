# ======================= FINAL FULL APP.PY =======================
# Includes:
#  - Text commands
#  - Reminders system
#  - History
#  - Web search backend
#  - Voice STT/TTS endpoints preserved
#  - Popup trigger stable

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import threading
import logging

from assistant import PersonalAssistant
from speech_handler import SpeechHandler
from reminder_manager import ReminderManager


app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("ASSISTANT")

# Services
reminder_manager = ReminderManager()
assistant = PersonalAssistant(reminder_manager=reminder_manager)
speech = SpeechHandler()

last_popup_sent = None


# ================================================================
#                      HEALTH + HOME ROUTES
# ================================================================
@app.route("/")
def home():
    return jsonify({"status": "OK", "features": 7})


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "server": "running",
        "reminders_active": len(reminder_manager.get_reminders()),
        "tts": True,
        "speech_input_available": speech.test_microphone()
    })


# ================================================================
#                     TEXT PROCESSING
# ================================================================
@app.route("/process", methods=["POST"])
def process_cmd():
    try:
        data = request.get_json()
        if "command" not in data:
            return jsonify({"success": False, "error": "Missing command"})

        cmd = data["command"]
        response = assistant.process_command(cmd)
        return jsonify({"success": True, "response": response})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ================================================================
#                    SPEECH TO TEXT (OPTIONAL BACKEND)
# ================================================================
@app.route('/listen', methods=['POST'])
def listen_command():
    try:
        options = request.get_json() or {}
        text = SpeechHandler.listen(
            timeout=options.get("timeout", 5),
            phrase_time_limit=options.get("phrase_time_limit", 10)
        )

        print("🟢 RAW SPEECH:", text)  # <= SEND THIS OUTPUT TO ME HERE

        if text.startswith("ERROR:"):
            return jsonify({"error": text, "success": False}), 400

        response = assistant.process_command(text)
        return jsonify({"command": text, "response": response, "success": True})

    except Exception as e:
        print("❌ Speech Recognition Crash:", e)
        return jsonify({"error": str(e), "success": False}), 500




# ================================================================
#                    TEXT TO SPEECH BACKEND
# ================================================================
@app.route("/speak", methods=["POST"])
def speak_out():
    """Still supported — but frontend TTS is used by default."""
    data = request.get_json()
    if "text" not in data:
        return jsonify({"success": False, "error": "Missing 'text'"})

    threading.Thread(target=speech.speak, args=(data["text"],), daemon=True).start()
    return jsonify({"success": True})


# ================================================================
#                    REMINDERS API
# ================================================================
@app.route("/reminders", methods=["GET"])
def list_reminders():
    r = reminder_manager.get_reminders()
    formatted = [{
        "id": item["id"],
        "text": item["text"],
        "time": item["time"].strftime("%I:%M %p %d-%b"),
    } for item in r]

    return jsonify({"success": True, "reminders": formatted})


@app.route("/reminders/<int:id>", methods=["DELETE"])
def delete_reminder(id):
    reminder_manager.delete_reminder(id)
    return jsonify({"success": True})


@app.route("/reminders/clear", methods=["DELETE"])
def clear_all():
    reminder_manager.clear_all()
    return jsonify({"success": True})


# ================= REMINDER POPUP EVENT API ===================
last_reminder_served = set()   # Track IDs already announced

@app.route("/trigger_popup", methods=["GET"])
def trigger_popup():
    reminders = reminder_manager.get_reminders_raw()

    for r in reminders:
        if r["triggered"] and not r.get("popup_acknowledged", False):
            r["popup_acknowledged"] = True  # prevents repeat popups

            return jsonify({
                "success": True,
                "message": r["text"],      # must be "message" for frontend
                "id": r["id"],
                "time": r["time"].strftime("%I:%M %p %d-%b")
            })

    return jsonify({"success": False})


# ================================================================
#                HISTORY
# ================================================================
@app.route("/history", methods=["GET", "DELETE"])
def history():
    if request.method == "DELETE":
        assistant.clear_history()
        return jsonify({"success": True})

    return jsonify({"success": True, "history": assistant.get_history()})


# ================================================================
# START REMINDER THREAD + SERVER
# ================================================================
# =================== RUN SERVER ===================
# ================================================================
# START REMINDER THREAD + SERVER
# ================================================================
if __name__ == '__main__':
    print("🚀 Flask API starting...")

    # <<< YOU WERE MISSING THIS >>>
    reminder_manager.start()   # background thread NOW running

    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port, threaded=True)
