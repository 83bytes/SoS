FROM --platform=linux/amd64 python:3.11-slim

# Install tini for proper signal handling
RUN apt-get update && apt-get install -y --no-install-recommends tini && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -g 1000 appuser && \
    useradd -r -u 1000 -g appuser appuser

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY metrics_generator.py .
COPY example_config.json .

# Create necessary directories
RUN mkdir -p /app/config && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Set environment variables
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

# Use tini as init system for proper signal handling
ENTRYPOINT ["tini", "--", "python3", "metrics_generator.py"]
CMD ["--port", "8000", "--verbose"]