# Use Python 3.13 slim as base
FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies (faiss, build deps etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY src ./src
COPY faiss_index.bin faiss_meta.pkl ./

# Install uv
RUN pip install uv

# Install dependencies into system environment from pyproject.toml
RUN uv pip install --system .

# Default command
CMD ["uv", "run", "src/main.py"]
