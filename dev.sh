#!/bin/bash

echo "Installing dependencies"
sudo apt install libreoffice ghostscript redis-server

echo "Creating migrations..."
pipenv run python manage.py makemigrations

echo "Migrating..."
pipenv run python manage.py migrate

echo "Starting Server..."
pipenv run python manage.py runserver 0.0.0.0:8000