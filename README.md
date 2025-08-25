# Swedish Live Transcribe + Translate

A minimal local web app that listens to mic, transcribes Swedish, and translates to English.

## Run

1) Start static server:
   python3 -m http.server 8080

2) Start local translator (first time downloads sv->en model):
   source .venv/bin/activate
   nohup python translate_server.py >/tmp/argos.log 2>&1 &

3) Open app:
   open http://localhost:8080

## Dev

- Frontend tries Local (Argos) → LibreTranslate → MyMemory.
- Interim translations update frequently; finals append as history.
- Per‑word panel streams whole-word translations.

## Project files

- index.html
- translate_server.py

