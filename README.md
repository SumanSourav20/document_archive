## Docker Setup

Install Docker Desktop(on the docker desktop application) and run the following command to start the application:

```sh
docker-compose up --build
```

Or in detached mode( use this -f docker-compose.yml file name)

```sh
docker compose up -d
```

If not using Docker, use Python 3.13 and configure PostgreSQL correctly:

```add it to .env
POSTGRES_HOST=localhost
POSTGRES_PORT=5433

include postgres data in .env

do 
pipenv install

python manage.py migrate

python manage.py runserver

```

---

## Authentication Endpoints

### Register a new user
**POST** `/register/`

```json
{
    "username": "",
    "email": "",
    "password": "",
    "password_confirm": ""
}
```

Upon successful registration, an activation link is sent via email.

### Activate account
**GET** `accounts/activate/<token>/`

### Request password reset
**POST** `accounts/password-reset/request/`

```json
{
    "email":""
}
```

```json
{
    "status": "success",
    "message": "OTP has been sent to your email.",
    "token": "......."
}```

Upon request, a token is returned, and an OTP is sent via email.

> **Issue:** This endpoint allows checking if an email is registered.

### Verify password reset
**POST** `accounts/password-reset/verify/`

```json
{
    "token": "",
    "otp": "",
    "new_password": "",
    "confirm_password": ""
}
```

> **Issue:** The old password can be reused.

---

## Authentication and Token Management

### Obtain access token(login)
**POST** `/api/token/`

{
    "refresh": "",
    "access": ""
}

### Refresh access token
**POST** `/api/token/refresh/`


{
    "refresh": "",
}