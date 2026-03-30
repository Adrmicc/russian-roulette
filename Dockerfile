# Russian Roulette — Multi-stage Dockerfile
# 1 Builder — install Python dependencies into a venv
# 2 Runtime — lean image with only the venv & app code

# 1 Builder
FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# 2 Runtime
FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="russian-roulette" \
    org.opencontainers.image.description="Flask Russian Roulette mini-game" \
    org.opencontainers.image.source="https://github.com/adrmicc/russian-roulette" \
    org.opencontainers.image.licenses="MIT"

# Create non-root user
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --create-home appuser

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY app.py .


USER appuser

EXPOSE 5000

# Health-check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

CMD ["python", "app.py"]
