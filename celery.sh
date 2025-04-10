#!/bin/bash

echo "Starting Celery worker..."
pipenv run celery -A document_archive worker