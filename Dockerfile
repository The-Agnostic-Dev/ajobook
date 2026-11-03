FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AJOBOOK_DATABASE_URL=sqlite:////data/ajobook.sqlite3 \
    AJOBOOK_SEED_DEMO=1

WORKDIR /srv/ajobook
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
RUN mkdir -p /data

EXPOSE 5111
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5111"]
