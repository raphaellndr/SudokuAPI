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

# Main execution
echo "Starting Django application..."

# Wait for database to be ready
wait_for_db

# Create migrations (only if needed)
echo "Creating any new migrations..."
python3 manage.py makemigrations

# Apply migrations
echo "Applying migrations..."
python3 manage.py migrate

# Start development server
echo "Starting development server..."
python3 manage.py runserver 0.0.0.0:8000 --traceback --verbosity 3
