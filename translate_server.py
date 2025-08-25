from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import argostranslate.package
import argostranslate.translate

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Make sure Argos uses writable data dir in containerized envs
os.environ.setdefault("HOME", BASE_DIR)
os.environ.setdefault("XDG_DATA_HOME", os.path.join(BASE_DIR, ".local", "share"))
app = Flask(__name__, static_folder=BASE_DIR, static_url_path="")
CORS(app)

# Ensure Swedish->English model is installed on first run
_initialized = False

def ensure_model():
    global _initialized
    if _initialized:
        return
    # Swedish (sv) to English (en)
    from_code, to_code = "sv", "en"
    installed = argostranslate.package.get_installed_packages()
    if not any(p.from_code == from_code and p.to_code == to_code for p in installed):
        # Download and install package
        available = argostranslate.package.get_available_packages()
        pkg = next((p for p in available if p.from_code == from_code and p.to_code == to_code), None)
        if not pkg:
            raise RuntimeError("No Argos package sv->en available")
        download_path = pkg.download()
        argostranslate.package.install_from_path(download_path)
    _initialized = True

@app.route("/health")
def health():
    return {"ok": True}

@app.route("/")
def index():
    # Serve the SPA
    return send_from_directory(BASE_DIR, "index.html")

@app.route("/translate", methods=["POST"]) 
def translate():
    ensure_model()
    data = request.get_json(force=True)
    text = (data.get("q") or data.get("text") or "").strip()
    source = (data.get("source") or "sv").strip()
    target = (data.get("target") or "en").strip()
    if not text:
        return jsonify({"translatedText": ""})
    translated = argostranslate.translate.translate(text, source, target)
    return jsonify({"translatedText": translated})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5009"))
    dev = str(os.environ.get("DEV", "0")).lower() in {"1","true","yes"}
    app.run(host="0.0.0.0", port=port, debug=dev, use_reloader=dev)
