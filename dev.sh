#!/bin/bash

echo "Creating migrations..."
pipenv run python manage.py makemigrations

echo "Migrating..."
pipenv run python manage.py migrate

echo "Starting Server..."
pipenv run python manage.py runserver 0.0.0.0:8000