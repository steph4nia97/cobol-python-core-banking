FROM python:3.12-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends gnucobol \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pytest.ini /app/pytest.ini
COPY python /app/python
COPY cobol /app/cobol

RUN pip install --no-cache-dir -e "./python[dev]"

EXPOSE 8000
CMD ["uvicorn", "banking_pipeline.api:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "python"]
