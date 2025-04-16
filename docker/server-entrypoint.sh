#!/bin/sh

until python manage.py migrate --fake-initial
do
    echo "Waiting for db to be ready..."
    sleep 2
done

if [ "$DJANGO_SUPERUSER_USERNAME" ]
then
    python3 manage.py createsuperuser \
        --noinput \
        --username $DJANGO_SUPERUSER_USERNAME \
        --email $DJANGO_SUPERUSER_EMAIL
fi

python3 manage.py runserver 0.0.0.0:8000