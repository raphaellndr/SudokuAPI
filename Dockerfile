ARG PYTHON_VERSION=3.12

#################
# Builder stage #
#################
FROM python:${PYTHON_VERSION}-alpine AS builder

# Set up environment
# First line is to enable running poetry without specifying the path
# Second line is to prevent Python from writing .pyc files
# Third line is to ensure that Python output is sent straight to the terminal
# Fourth line is to pin the Poetry version
ENV PATH="/root/.local/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.1.1

# Install system dependencies and pipx
RUN apk add --no-cache \
    pipx \
    git \
    build-base \
    libffi-dev \
    # clean up
    && rm -rf /var/cache/apk/*

# Install poetry with pipx and inject poetry-plugin-bundle
RUN pipx install poetry==${POETRY_VERSION}
RUN pipx inject poetry poetry-plugin-bundle

WORKDIR /src
COPY . .

# Bundle dependencies into a virtual environment
RUN poetry bundle venv /venv

####################
# Web server image #
####################
FROM python:${PYTHON_VERSION}-alpine AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/venv/bin:${PATH}"

# Copy virtual environment from builder
COPY --from=builder /venv /venv
COPY --from=builder /src/app /app

ENTRYPOINT ["/venv/bin/python3"]
