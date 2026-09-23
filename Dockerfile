FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system almond \
    && adduser --system --ingroup almond almond

COPY pyproject.toml ./
COPY src ./src
COPY web ./web
COPY constraints.yaml ./constraints.yaml

RUN python -m pip install .

USER almond

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).read()"]

CMD ["uvicorn", "almond.api:app", "--host", "0.0.0.0", "--port", "8000"]
