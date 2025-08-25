from flask import Flask, request, jsonify
from flask_cors import CORS
import argostranslate.package
import argostranslate.translate

app = Flask(__name__)
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
    app.run(host="127.0.0.1", port=5009)
