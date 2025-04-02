from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    profile_pic = models.TextField(null=True, blank=True) # or avtar
    
    def get_full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    def __str__(self):
        full_name = self.get_full_name().strip()
        if not full_name:
            return self.user.username
        return full_name
