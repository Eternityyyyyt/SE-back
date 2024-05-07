#!/bin/sh
python3 manage.py makemigrations user chat
python3 manage.py migrate

#Run with uWSGI
uwsgi --module=SE-back.wsgi:application \
    --env DJANGO_SETTINGS_MODULE=SE-back.settings \
    --master \
    --http=0.0.0.0:80 \
    --processes=5 \
    --harakiri=20 \
    --max-requests=5000 \
    --vacuum


# # Uvicorn arguments
# UVICORN_ARGS="--host 0.0.0.0 --port 80 --workers 5"

# # The application to run
# APPLICATION="SE-back.asgi:application"

# # Run Uvicorn with the specified arguments and application
# uvicorn $APPLICATION$UVICORN_ARGS
