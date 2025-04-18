from django.core.mail import send_mail
from django.conf import settings

import jwt
from cryptography.fernet import Fernet
import random
import string
from datetime import datetime, timedelta

ENCRYPTION_KEY = settings.ENCRYPTION_KEY

fernet = Fernet(ENCRYPTION_KEY)

def create_verification_token(user_id, email):
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.now() + timedelta(days=1) 
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    
    encrypted_token = fernet.encrypt(token.encode())
    return encrypted_token.decode()

def verify_token(encrypted_token):
    try:
        token = fernet.decrypt(encrypted_token.encode()).decode()
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        
        return True, payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return False, None
    except Exception:
        return False, None

def send_welcome_email(user, request):
    token = create_verification_token(user.id, user.email)
    
    host = request.get_host()
    verification_url = f"http://{host}/api/accounts/activate/{token}/"
    
    subject = "Verify Your Email Address"
    message = (
        f"Hello {user.first_name or user.username},\n\n"
        "Thank you for registering with us!\n\n"
        f"Click on the link below to verify your email and activate your account:\n{verification_url}\n\n"
        "This link is valid for 24 hours.\n\n"
        "Best Regards,\nYour Team"
    )
    
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

def create_reset_token(user_id, email, otp):
    payload = {
        'user_id': user_id,
        'email': email,
        'otp': otp,
        'exp': datetime.now() + timedelta(minutes=5)
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    
    encrypted_token = fernet.encrypt(token.encode())
    return encrypted_token.decode()

def verify_reset_token(encrypted_token, submitted_otp):
    try:
        token = fernet.decrypt(encrypted_token.encode()).decode()
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        
        if payload['otp'] == submitted_otp:
            return True, payload
        return False, None
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return False, None
    except Exception:
        return False, None

def send_otp_email(email, otp):
    subject = "Password Reset OTP"
    message = (
        f"Your OTP for password reset is: {otp}\n\n"
        "This code is valid for 5 minutes.\n\n"
        "If you didn't request this, please ignore this email.\n\n"
        "Best Regards,\nYour Team"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)