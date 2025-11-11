# Multi-stage Dockerfile for Player Account API Lambda
# Builds with uv package manager for Python 3.13
# Optimized for AWS Lambda container image deployment

# Stage 1: Builder - Install dependencies and build the package
FROM public.ecr.aws/lambda/python:3.13 AS builder

# Use specific uv version for reproducible builds
ARG UV_VERSION=0.5.6
# Download and install uv package manager
RUN pip install uv==${UV_VERSION}

# Set build arguments for cache busting
ARG BUILD_DATE
ARG VCS_REF

# Add labels for metadata
LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.schema-version="1.0" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/andybuit/python_lambdas" \
      org.label-schema.vendor="PSN Partner Emulator" \
      org.label-schema.name="fips-psn-player-account-api" \
      org.label-schema.description="Player Account API Lambda for PSN Emulator"

# Set working directory
WORKDIR /build

# Install dependencies in layers for better caching
# First, copy only dependency files to leverage Docker layer caching
COPY libs/common/pyproject.toml libs/common/pyproject.toml
COPY services/player_account_api/pyproject.toml services/player_account_api/pyproject.toml

# Install Lambda dependencies first (changes less frequently)
RUN cd services/player_account_api && \
    uv sync --no-dev && \
    uv cache prune --ci

# Copy source code (changes more frequently)
COPY libs/common/src/ libs/common/src/
COPY services/player_account_api/src/ services/player_account_api/src/

# Install the common library from local path
RUN cd services/player_account_api && \
    uv pip install /build/libs/common && \
    chmod -R 755 /build/services/player_account_api/.venv

# Stage 2: Runtime - Copy only necessary files to final image
FROM public.ecr.aws/lambda/python:3.13

# Add runtime labels
LABEL org.label-schema.name="fips-psn-player-account-api-runtime" \
      org.label-schema.description="Runtime image for Player Account API Lambda"

# Set environment variables for Lambda runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH="/var/task:/var/task/libs/common/src" \
    POWERTOOLS_SERVICE_NAME=player-account-api \
    POWERTOOLS_LOG_LEVEL=INFO \
    LAMBDA_TASK_ROOT=/var/task

# Copy Python dependencies from builder stage
COPY --from=builder /build/services/player_account_api/.venv/lib/python3.13/site-packages/ ${LAMBDA_TASK_ROOT}/

# Copy Lambda source code
COPY --from=builder /build/services/player_account_api/src/ ${LAMBDA_TASK_ROOT}/

# Copy common library source
COPY --from=builder /build/libs/common/src/ ${LAMBDA_TASK_ROOT}/libs/common/src/

# Set working directory for Lambda runtime
WORKDIR ${LAMBDA_TASK_ROOT}

# Add health check for local testing
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9000/2015-03-31/functions/function/invocations || exit 1

# Lambda handler (AWS Lambda looks for this in the root)
CMD ["handler.lambda_handler"]
