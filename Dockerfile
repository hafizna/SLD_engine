# Runs on any container host.
#  - local / docker-compose      : PORT defaults to 8000
#  - Hugging Face Spaces (Docker) : Spaces sets PORT=7860
#  - Render / Railway / Fly       : they inject PORT
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# SQLite seeded on boot (SS_LBK). Override DATABASE_URL for Postgres.
ENV DATABASE_URL=sqlite:////tmp/mantaps.db
ENV PORT=7860
EXPOSE 7860

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
