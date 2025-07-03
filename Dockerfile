# syntax=docker/dockerfile:1

############## builder ################
FROM python:3.11-slim AS builder

WORKDIR /app

# System deps for building wheels (faiss, psycopg2, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential gcc wget curl git && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps into a user-layer to copy later
COPY requirements.txt ./
RUN pip install --user --no-warn-script-location --no-cache-dir -r requirements.txt

############## runtime ################
FROM python:3.11-slim
LABEL maintainer="Smart Building AI"

ENV PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:$PATH" \
    PORT=8501

WORKDIR /app

# Copy python packages from builder stage
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Minimal runtime system libs (for PDF parsing & others)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libglib2.0-0 libstdc++6 && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 8501

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port 8000 & streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0"] 