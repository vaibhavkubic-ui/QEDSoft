FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml README.md requirements.txt ./
COPY src ./src
RUN pip install --no-cache-dir -e ".[api]"

EXPOSE 8080
CMD ["uvicorn", "qedsoft.api.server:app", "--host", "0.0.0.0", "--port", "8080"]
