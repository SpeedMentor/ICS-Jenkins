FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN adduser --disabled-password --gecos "" --home /app appuser

WORKDIR /app

COPY requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir aiofiles

COPY main.py ./main.py
COPY static ./static

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 9001

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9001", "--proxy-headers"]
