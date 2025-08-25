# Swedish Live Transcribe + Translate

A minimal local web app that listens to mic, transcribes Swedish, and translates to English.

## Run

1) Start the combined server (serves UI and /translate):
   source .venv/bin/activate
   python translate_server.py

2) Open app:
   open http://localhost:5009

## Dev

- Frontend tries Local (Argos) → LibreTranslate → MyMemory.
- Interim translations update frequently; finals append as history.
- Per‑word panel streams whole-word translations.

## Deploy

Option A: Docker (recommended)

```
docker build -t live-translator .
docker run -p 8080:8080 -e PORT=8080 live-translator
```

Option B: Render, Fly.io, Railway, Heroku
- Render: click this and follow the prompts (connect your repo):

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

- Or on any platform, use the Dockerfile or set `PORT` and run `python translate_server.py`.

Option C: Instant local tunnel (temporary public URL)

```
npx localtunnel --port 5009
```

## Project files

- index.html
- translate_server.py

