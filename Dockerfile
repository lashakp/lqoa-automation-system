# Use lightweight Python base
FROM python:3.10-slim

# -----------------------------
# Environment settings
# -----------------------------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# -----------------------------
# System dependencies
# -----------------------------
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# Set working directory
# -----------------------------
WORKDIR /app

# -----------------------------
# Install Python dependencies
# -----------------------------
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# -----------------------------
# Copy project files
# -----------------------------
COPY . .

# -----------------------------
# Render requires dynamic port binding
# -----------------------------
EXPOSE 10000

# -----------------------------
# Start FastAPI app (Render-compatible)
# -----------------------------
CMD ["sh", "-c", "uvicorn pipeline.api.app:app --host 0.0.0.0 --port ${PORT:-10000}"]