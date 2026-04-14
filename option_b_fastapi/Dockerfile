FROM python:3.11-slim

WORKDIR /app

COPY option_b_fastapi/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY core/ /app/core/
COPY option_b_fastapi/ /app/option_b_fastapi/

EXPOSE 8000

CMD ["sh", "-c", "uvicorn option_b_fastapi.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-2}"]
