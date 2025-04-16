#!/bin/sh

until python manage.py migrate --fake-initial
do
    echo "Waiting for db to be ready..."
    sleep 2
done

python3 manage.py runserver 0.0.0.0:8000