FROM python:3.11-slim

WORKDIR /app

# Install dependencies in a separate layer for better caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source and install package (non-editable, more reliable in CI/Docker)
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir --no-deps .

EXPOSE 8080
CMD ["uvicorn", "qedsoft.api.server:app", "--host", "0.0.0.0", "--port", "8080"]
