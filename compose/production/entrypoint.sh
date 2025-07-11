#!/bin/sh

set -o errexit
set -o nounset

# Function to wait for database
wait_for_db() {
    echo "Waiting for database to be ready..."
    while ! python3 manage.py check --database default > /dev/null 2>&1; do
        echo "Database unavailable - sleeping"
        sleep 2
    done
    echo "Database is ready!"
}

# Function to run migrations safely
run_migrations() {
    echo "Running database migrations..."
    python3 manage.py migrate --noinput
}

# Function to collect static files
collect_static() {
    echo "Collecting static files..."
    python3 manage.py collectstatic --noinput --clear
}

# Main execution
echo "Starting Django application..."

# Wait for database to be ready
wait_for_db

# Run migrations
run_migrations

# Collect static files
collect_static

echo "Starting server..."
python3 manage.py runserver 0.0.0.0:$PORT
