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
    """Lazy-load Argos modules once. Do NOT install models here to avoid runtime 500s."""
    global _initialized, _argos_package, _argos_translate
    if _initialized:
        return
    from argostranslate import package as _pkg
    from argostranslate import translate as _tr
    _argos_package = _pkg
    _argos_translate = _tr
    _initialized = True

@app.route("/health")
def health():
    return {"ok": True}

@app.route("/version")
def version():
    ts = os.environ.get("DEPLOY_TS", "unknown")
    return {
        "version": os.environ.get("GIT_TAG", "v2"),
        "deployed_at": ts,
        "build": os.environ.get("BUILD_NUM", os.environ.get("GIT_SHA", "dev"))
    }

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
    def _has_pair(fc, tc):
        try:
            return any(p.from_code == fc and p.to_code == tc for p in _argos_package.get_installed_packages())
        except Exception:
            return False

    def translate_once(src, tgt, txt):
        return _argos_translate.translate(txt, src, tgt)

    try:
        if source == target:
            return jsonify({"translatedText": text})
        # Prefer direct if installed
        if _has_pair(source, target):
            out = translate_once(source, target, text)
            return jsonify({"translatedText": out})
        # Pivot via English if possible
        if source != "en" and target != "en" and _has_pair(source, "en") and _has_pair("en", target):
            mid = translate_once(source, "en", text)
            out = translate_once("en", target, mid)
            return jsonify({"translatedText": out})
        # Fallback attempt even if not declared installed (may work if packed)
        try:
            out = translate_once(source, target, text)
            return jsonify({"translatedText": out})
        except Exception:
            pass
    except Exception as e:
        print("translate error:", e)
    # Graceful response to avoid client 500s
    return jsonify({"translatedText": ""})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5009"))
    dev = str(os.environ.get("DEV", "0")).lower() in {"1","true","yes"}
    app.run(host="0.0.0.0", port=port, debug=dev, use_reloader=dev, threaded=True)
