FROM python:3.11-slim AS builder

RUN apt-get update && \
    apt-get install -y curl git build-essential ffmpeg && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/* && \
    mkdir -p /Whisper-WebUI-Swear-Removal

WORKDIR /Whisper-WebUI-Swear-Removal

COPY backend/ backend/
COPY requirements.txt requirements.txt

RUN python -m venv venv && \
    . venv/bin/activate && \
    pip install --upgrade pip && \
    pip install "setuptools<58" wheel cython && \
    export PIP_NO_BUILD_ISOLATION=false && \
    pip install -U -r backend/requirements-backend.txt


FROM python:3.11-slim AS runtime

RUN apt-get update && \
    apt-get install -y curl ffmpeg && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Create non-root user and necessary directories
RUN useradd -m -u 1000 appuser && \
    mkdir -p /home/appuser/.cache/huggingface && \
    mkdir -p /home/appuser/.config/matplotlib && \
    mkdir -p /Whisper-WebUI-Swear-Removal && \
    chown -R appuser:appuser /home/appuser && \
    chown -R appuser:appuser /Whisper-WebUI-Swear-Removal

WORKDIR /Whisper-WebUI-Swear-Removal

COPY --chown=appuser:appuser . .
COPY --from=builder --chown=appuser:appuser /Whisper-WebUI-Swear-Removal/venv /Whisper-WebUI-Swear-Removal/venv

# Set proper permissions for volumes
RUN mkdir -p /Whisper-WebUI-Swear-Removal/models /Whisper-WebUI-Swear-Removal/outputs /Whisper-WebUI-Swear-Removal/backend && \
    chown -R appuser:appuser /Whisper-WebUI-Swear-Removal

VOLUME [ "/Whisper-WebUI-Swear-Removal/models" ]
VOLUME [ "/Whisper-WebUI-Swear-Removal/outputs" ]
VOLUME [ "/Whisper-WebUI-Swear-Removal/backend" ]

# Set environment variables for cache and config directories
ENV PATH="/Whisper-WebUI-Swear-Removal/venv/bin:$PATH"
ENV LD_LIBRARY_PATH=/Whisper-WebUI-Swear-Removal/venv/lib64/python3.11/site-packages/nvidia/cublas/lib:/Whisper-WebUI-Swear-Removal/venv/lib64/python3.11/site-packages/nvidia/cudnn/lib
ENV HF_HOME="/home/appuser/.cache/huggingface"
ENV MPLCONFIGDIR="/home/appuser/.config/matplotlib"
ENV PYTHONPATH="/Whisper-WebUI-Swear-Removal"

USER appuser

ENTRYPOINT ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
