FROM python:3.13.2-slim

WORKDIR /app

RUN pip install --no-cache-dir pipenv

RUN apt-get update && apt-get install -y libmagic-dev libreoffice ghostscript

COPY Pipfile* ./

RUN pipenv install --python $(which python)

RUN pipenv install

COPY . .

EXPOSE 8000

COPY production.sh ./
RUN chmod +x production.sh

CMD ["pipenv", "run", "gunicorn", "document_archvie.wsgi:application", "--bind", "0.0.0.0:8000"]
