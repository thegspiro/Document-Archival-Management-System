FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libmagic1 \
    poppler-utils \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Siegfried for format characterization
RUN wget -qO - https://bintray.com/user/downloadSubjectPublicKey?username=siegfried | apt-key add - || true
RUN curl -sL "https://github.com/richardlehane/siegfried/releases/download/v1.11.1/siegfried_1.11.1-1_amd64.deb" -o /tmp/siegfried.deb \
    && dpkg -i /tmp/siegfried.deb || true \
    && rm -f /tmp/siegfried.deb

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]" 2>/dev/null || pip install --no-cache-dir .

COPY . .

RUN adduser --disabled-password --gecos '' appuser
RUN mkdir -p /data/storage && chown -R appuser:appuser /data/storage
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
