FROM ubuntu:24.04

WORKDIR /app

RUN apt-get update && apt-get install -y \
    software-properties-common \
    libmagic-dev \
    libreoffice \
    ghostscript \
    redis-server \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get update \
    && apt-get install -y python3.13

RUN apt install pipenv -y

COPY Pipfile* ./

RUN PIPENV_VENV_IN_PROJECT=1 pipenv --python /usr/bin/python3.13 install

COPY . .

EXPOSE 8000

RUN chmod +x ./dev.sh

CMD ["./dev.sh"]