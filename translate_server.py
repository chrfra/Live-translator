from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Make sure Argos uses writable data dir in containerized envs
os.environ.setdefault("HOME", BASE_DIR)
os.environ.setdefault("XDG_DATA_HOME", os.path.join(BASE_DIR, ".local", "share"))
app = Flask(__name__)
CORS(app)

# Ensure Swedish->English model is installed on first run
_initialized = False
_argos_package = None
_argos_translate = None

def ensure_model():
    global _initialized, _argos_package, _argos_translate
    if _initialized:
        return
    # Lazy import heavy modules
    from argostranslate import package as _pkg
    from argostranslate import translate as _tr
    _argos_package = _pkg
    _argos_translate = _tr
    # Swedish (sv) to English (en)
    from_code, to_code = "sv", "en"
    installed = _argos_package.get_installed_packages()
    if not any(p.from_code == from_code and p.to_code == to_code for p in installed):
        # Download and install package
        available = _argos_package.get_available_packages()
        pkg = next((p for p in available if p.from_code == from_code and p.to_code == to_code), None)
        if not pkg:
            raise RuntimeError("No Argos package sv->en available")
        download_path = pkg.download()
        _argos_package.install_from_path(download_path)
    _initialized = True

@app.route("/health")
def health():
    return {"ok": True}

@app.route("/")
def index():
    return send_file(os.path.join(BASE_DIR, "index.html"))

@app.route("/index.html")
def index_html():
    return send_file(os.path.join(BASE_DIR, "index.html"))

@app.route("/favicon.ico")
def favicon():
    # Avoid 404 noise
    return ("", 204)

@app.route("/translate", methods=["GET","POST","OPTIONS"]) 
def translate():
    # Handle preflight/OPTIONS explicitly to avoid 501/405 from proxies
    if request.method == "OPTIONS":
        return ("", 204)
    ensure_model()
    if request.method == "GET":
        text = (request.args.get("q") or request.args.get("text") or "").strip()
        source = (request.args.get("source") or "sv").strip()
        target = (request.args.get("target") or "en").strip()
    else:
        data = request.get_json(silent=True) or {}
        text = (data.get("q") or data.get("text") or "").strip()
        source = (data.get("source") or "sv").strip()
        target = (data.get("target") or "en").strip()
    if not text:
        return jsonify({"translatedText": ""})
    translated = _argos_translate.translate(text, source, target)
    return jsonify({"translatedText": translated})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5009"))
    dev = str(os.environ.get("DEV", "0")).lower() in {"1","true","yes"}
    app.run(host="0.0.0.0", port=port, debug=dev, use_reloader=dev, threaded=True)
