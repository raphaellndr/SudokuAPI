#!/bin/sh

set -o errexit
set -o nounset

until python3 manage.py migrate --fake-initial
do
    echo "Waiting for db to be ready..."
    sleep 2
done

python3 manage.py runserver 0.0.0.0:8000 --traceback --verbosity 3