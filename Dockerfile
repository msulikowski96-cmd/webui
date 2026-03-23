FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ git curl ffmpeg libmagic1 libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir \
    "open-webui" \
    "psycopg2-binary" \
    --extra-index-url https://download.pytorch.org/whl/cpu

COPY start.sh .
RUN chmod +x start.sh

EXPOSE 5000

CMD ["bash", "start.sh"]
