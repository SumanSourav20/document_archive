from django.core.validators import RegexValidator

strong_password_validator = RegexValidator(
    regex=r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$',
    message='Password must be at least 8 characters long and include one uppercase letter, one lowercase letter, and one number.'
)