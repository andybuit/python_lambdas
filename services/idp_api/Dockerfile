# Multi-stage Dockerfile for IDP API Lambda
# Builds with uv package manager for Python 3.13

# Stage 1: Builder - Install dependencies and build the package
FROM public.ecr.aws/lambda/python:3.13 AS builder

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /build

# Copy common library files first (dependency)
COPY libs/common/pyproject.toml libs/common/
COPY libs/common/src libs/common/src

# Copy Lambda-specific files
COPY services/idp_api/pyproject.toml services/idp_api/
COPY services/idp_api/src services/idp_api/src

# Change to Lambda directory
WORKDIR /build/services/idp_api

# Install dependencies using uv
# This creates a .venv with all dependencies
RUN uv sync --no-dev --frozen

# Install the common library from local path
RUN uv pip install /build/libs/common

# Stage 2: Runtime - Copy only necessary files to final image
FROM public.ecr.aws/lambda/python:3.13

# Copy Python dependencies from builder
COPY --from=builder /build/services/idp_api/.venv/lib/python3.13/site-packages/ ${LAMBDA_TASK_ROOT}/

# Copy Lambda source code
COPY services/idp_api/src/ ${LAMBDA_TASK_ROOT}/

# Copy common library source
COPY --from=builder /build/libs/common/src/ ${LAMBDA_TASK_ROOT}/libs/common/src/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV POWERTOOLS_SERVICE_NAME=idp-api

# Lambda handler
CMD ["handler.lambda_handler"]
