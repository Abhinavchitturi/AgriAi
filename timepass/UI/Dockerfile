# AgriAI Assistant UI - Dockerfile
# Multi-stage build for optimized production image

# ============================================================================
# Stage 1: Base Python Environment
# ============================================================================
FROM python:3.9-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# Stage 2: Development Environment
# ============================================================================
FROM base as development

# Create non-root user
RUN useradd --create-home --shell /bin/bash agriuser

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY . .

# Change ownership to non-root user
RUN chown -R agriuser:agriuser /app
USER agriuser

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Default command for development
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]

# ============================================================================
# Stage 3: Production Environment
# ============================================================================
FROM base as production

# Install only production dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN useradd --create-home --shell /bin/bash --uid 1001 agriuser

# Set working directory
WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Install Python dependencies with optimizations
RUN pip install --upgrade pip && \
    pip install --no-dev -r requirements.txt && \
    pip cache purge

# Copy only necessary application files
COPY app.py config.py api_client.py utils.py ./

# Create necessary directories
RUN mkdir -p logs backups && \
    chown -R agriuser:agriuser /app

# Switch to non-root user
USER agriuser

# Set production environment variables
ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Production command
CMD ["streamlit", "run", "app.py", \
     "--server.address", "0.0.0.0", \
     "--server.port", "8501", \
     "--server.headless", "true", \
     "--server.enableCORS", "false", \
     "--server.enableXsrfProtection", "false"]

# ============================================================================
# Usage Instructions
# ============================================================================

# Build development image:
# docker build --target development -t agri-ai-ui:dev .

# Build production image:
# docker build --target production -t agri-ai-ui:prod .

# Run development container:
# docker run -p 8501:8501 -v $(pwd):/app agri-ai-ui:dev

# Run production container:
# docker run -p 8501:8501 -e API_BASE_URL=http://backend:8000 agri-ai-ui:prod

# Run with custom configuration:
# docker run -p 8501:8501 \
#   -e API_BASE_URL=https://api.example.com \
#   -e DEBUG=false \
#   -e ENABLE_MOCK_API=false \
#   agri-ai-ui:prod

# Docker Compose example:
# version: '3.8'
# services:
#   agri-ui:
#     build:
#       context: .
#       target: production
#     ports:
#       - "8501:8501"
#     environment:
#       - API_BASE_URL=http://backend:8000
#       - DEBUG=false
#     depends_on:
#       - backend
#     restart: unless-stopped