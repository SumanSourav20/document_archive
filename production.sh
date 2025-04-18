
echo "Creating migrations..."
pipenv run python manage.py makemigrations

echo "Migrating..."
pipenv run python manage.py migrate

echo "Collecting static files..."
pipenv run python manage.py collectstatic --noinput

echo "Starting Server..."
pipenv run gunicorn document_archive.wsgi:application --bind 0.0.0.0:8000
