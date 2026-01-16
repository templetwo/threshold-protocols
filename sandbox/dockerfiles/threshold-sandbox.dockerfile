# Threshold Protocols Sandbox Container
# =====================================
#
# Minimal, secure container for running threshold detection and simulation.
#
# Security features:
# - Non-root user
# - Read-only root filesystem (where possible)
# - No network by default (controlled by sandbox_manager)
# - Minimal attack surface (slim base)
#
# Build:
#   docker build -f threshold-sandbox.dockerfile -t threshold-sandbox:latest .
#
# Usage (via sandbox_manager.py - not directly):
#   docker run --rm --network=none -v ./workspace:/sandbox threshold-sandbox:latest

FROM python:3.11-slim

# Security: Create non-root user
RUN groupadd -r sandbox && useradd -r -g sandbox sandbox

# Install minimal dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /sandbox

# Copy requirements (if available in build context)
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt || true

# Security: Switch to non-root user
USER sandbox

# Default entrypoint
ENTRYPOINT ["python"]
CMD ["--help"]

# Labels for identification
LABEL org.threshold-protocols.version="0.1.0"
LABEL org.threshold-protocols.description="Sandbox container for threshold protocol testing"
LABEL org.threshold-protocols.security="non-root, network-isolated by default"
