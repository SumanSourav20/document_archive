from rest_framework import viewsets, permissions, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import Profile
from .serializers import (
    RegisterSerializer, 
    ProfileSerializer, 
    PasswordResetRequestSerializer, 
    PasswordResetVerifySerializer,
    ProfileListSerializer,
)
from .utils import (
    send_welcome_email,
    verify_token,
    generate_otp,
    create_reset_token,
    send_otp_email,
    verify_reset_token,
)
from django.db import transaction


from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .serializers import RegisterSerializer

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request):
        with transaction.atomic():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            profile = serializer.save()
            
            try:
                send_welcome_email(profile.user, request)

            except Exception as e:
                transaction.set_rollback(True)
                return Response(
                    {"status": "FAILED", "error": "Error sending email"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
            data = {
                "profile": {
                    "id": profile.id,
                    "username": profile.user.username,
                    "email": profile.user.email,
                },
                "message": "User registered successfully, verification mail send successfully"
            }
        
        return Response(data, status=status.HTTP_201_CREATED)

class ActivateUserView(views.APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, token):
        is_valid, payload = verify_token(token)
        
        if not is_valid:
            return Response({
                "status": "failed",
                "message": "Invalid or expired verification link."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=payload['user_id'], email=payload['email'])
            
            if not user.is_active:
                user.is_active = True
                user.save()
            
            return Response({
                "status": "success",
                "message": "Email verified successfully. Your account is now active."
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                "status": "failed",
                "message": "User not found."
            }, status=status.HTTP_404_NOT_FOUND)
            
class PasswordResetRequestView(views.APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                with transaction.atomic():
                    user = User.objects.get(email=email, is_active=True)
                    
                    otp = generate_otp()
                    
                    token = create_reset_token(user.id, email, otp)
                    
                    send_otp_email(email, otp)
                    
                    return Response({
                        "status": "success",
                        "message": "OTP has been sent to your email.",
                        "token": token
                    }, status=status.HTTP_200_OK)
                    
            except Exception as e:
                return Response({
                    "status": "failed", 
                    "error": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetVerifyView(views.APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetVerifySerializer(data=request.data)
        
        if serializer.is_valid():
            token = serializer.validated_data['token']
            otp = serializer.validated_data['otp']
            new_password = serializer.validated_data['new_password']
            
            is_valid, payload = verify_reset_token(token, otp)
            
            if not is_valid:
                return Response({
                    "status": "failed",
                    "error": "Invalid or expired OTP."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                with transaction.atomic():
                    user = User.objects.get(id=payload['user_id'], email=payload['email'])
                    
                    user.set_password(new_password)
                    user.save()
                    
                    return Response({
                        "status": "success",
                        "message": "Password has been reset successfully."
                    }, status=status.HTTP_200_OK)
                    
            except User.DoesNotExist:
                return Response({
                    "status": "failed",
                    "error": "User not found."
                }, status=status.HTTP_404_NOT_FOUND)
                
            except Exception as e:
                return Response({
                    "status": "failed",
                    "error": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return ProfileListSerializer
        return ProfileSerializer
    
    def get_queryset(self):
        return Profile.objects.filter(user__is_active=True)
    
    def get_object(self):
        return self.request.user.profile
    
    def create(self, request):
        return Response(
            {"detail": "Profiles are created automatically during registration."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        try:
            user_profile = request.user.profile
            serializer = self.get_serializer(user_profile)
            return Response(serializer.data)
        except Profile.DoesNotExist:
            return Response(
                {"detail": "Profile not found for current user."},
                status=status.HTTP_404_NOT_FOUND
            )
        
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
    
    def destroy(self, request):
        profile = self.get_object()
        user = profile.user
        user.is_active = False
        user.save()
        return Response(
            {"detail": "Your profile has been deactivated."},
            status=status.HTTP_200_OK
        )