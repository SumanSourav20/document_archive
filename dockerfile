FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir pipenv

RUN apt-get update && apt-get install -y libmagic-dev

COPY Pipfile* ./

RUN pipenv install

COPY . .

EXPOSE 8000

COPY dev.sh ./
RUN chmod +x dev.sh

CMD ["./dev.sh"]
