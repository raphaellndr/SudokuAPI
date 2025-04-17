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

# Set working directory to /src
WORKDIR /src

# Install system dependencies and pipx
RUN apk add --update --no-cache \
        pipx \
        git \
        libffi-dev && \
    apk add --update --no-cache --virtual .tmp-build-deps \
        build-base postgresql-dev musl-dev

# Install poetry with pipx and inject poetry-plugin-bundle
RUN pipx install poetry==${POETRY_VERSION}
RUN pipx inject poetry poetry-plugin-bundle

# Copy every necessary file to the image
COPY pyproject.toml poetry.lock manage.py README.md ./
COPY app ./app/
COPY config ./config/
COPY compose/production/celery/* compose/production/entrypoint.sh ./

# Bundle dependencies into a virtual environment
RUN poetry bundle venv /venv --with production

# Clean up
RUN rm -rf /var/cache/apk/* && apk del .tmp-build-deps

####################
# Web server image #
####################
FROM python:${PYTHON_VERSION}-alpine AS runtime

ENV PATH="/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory to /src
WORKDIR /src
    
# Install system dependencies
RUN apk add --update --no-cache postgresql-libs

# Create a non-root user and group
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Copy virtual environment from builder
COPY --from=builder /venv /venv
COPY --from=builder /src .

RUN sed -i 's/\r$//g' ./entrypoint.sh
RUN chmod +x ./entrypoint.sh 

RUN sed -i 's/\r$//g' ./worker-entrypoint.sh
RUN chmod +x ./worker-entrypoint.sh

RUN sed -i 's/\r$//g' ./beat-entrypoint.sh
RUN chmod +x ./beat-entrypoint.sh

# Set directories ownership to the non-root user
RUN chown -R appuser:appgroup /src /venv

WORKDIR /src/app
USER appuser
