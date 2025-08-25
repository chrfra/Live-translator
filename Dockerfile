FROM python:3.11-slim

# Prevents Python from writing .pyc files and buffers stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOME=/app \
    XDG_DATA_HOME=/app/.local/share

WORKDIR /app

COPY requirements.txt ./
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates build-essential \
    && pip install --upgrade pip \
    && pip install -r requirements.txt \
    && apt-get purge -y build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY . .

# Ensure writable data dirs for Argos Translate
RUN mkdir -p /app/.local/share && chmod -R 777 /app/.local || true

# Pre-install Argos sv->en model during build to avoid runtime downloads
RUN python - <<'PY'
import sys
try:
    from argostranslate import package
    pkgs = package.get_available_packages()
    target = next(p for p in pkgs if p.from_code == 'sv' and p.to_code == 'en')
    path = target.download()
    package.install_from_path(path)
    print('Installed Argos package:', target)
except Exception as e:
    print('Argos preinstall warning:', e, file=sys.stderr)
PY

# Use PORT provided by platform; default 8080
ENV PORT=8080
EXPOSE 8080

CMD exec gunicorn -w 2 -b 0.0.0.0:${PORT} translate_server:app

