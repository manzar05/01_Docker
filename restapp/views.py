from .models import *
from .serializers import *
from django.http import HttpResponse, Http404
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view,permission_classes
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from django.contrib.auth.hashers import make_password
from datetime import datetime,timedelta,timezone
import jwt
from django.core.exceptions import ValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
# Custom Services Import
from django.utils.http import urlsafe_base64_decode
from django.conf import settings
from django.utils.encoding import force_str
from restapp.services.email_service import send_verification_email

DOMAIN_URL='127.0.0.1:8000'
COMPANY='Manzar Organization'


# Override default Class for token generation
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        serializer=UserSerializerWithToken(self.user).data
        for k,v in serializer.items():
            data[k]=v       
        return data
    

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class=MyTokenObtainPairSerializer

@api_view(['GET'])
def home(request):
    data = {
        "message":"Successs"
    }
    return Response(data,status=status.HTTP_200_OK)

from django.contrib.auth import authenticate
@api_view(['POST'])
def loginUser(request):
    data = request.data
    if not data['username']:
        raise "Email Required"
    elif not data['password']:
        raise "Password Required"
    
    # Validate incoming data with serializer
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    username = serializer.validated_data['username']
    password = serializer.validated_data['password']
    
    # Authenticate user
    user = authenticate(username=username, password=password)
    if user is not None:
        serialize = UserSerializerWithToken(user, many=False).data
        return Response(serialize,status=status.HTTP_200_OK)
    data = {
        "message":"Login Failed"
    }
    return Response(data,status=status.HTTP_200_OK)


@api_view(['POST'])
def registerUser(request):
    data = request.data
    try:
        # Retrieve fields individually with default values or raise specific exceptions
        first_name = data.get('fname')
        if not first_name:
            raise DRFValidationError({'fname': 'First name is required.'})
        
        last_name = data.get('lname')
        if not last_name:
            raise DRFValidationError({'lname': 'Last name is required.'})
        
        username = data.get('email')
        if not username:
            raise DRFValidationError({'username': 'Username (email) is required.'})
        
        email = data.get('email')
        if not email:
            raise DRFValidationError({'email': 'Email is required.'})
        
        password = data.get('password')
        if not password:
            raise DRFValidationError({'password': 'Password is required.'})

        # Create user with validated fields
        user = MyUserTable.objects.create(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=make_password(password),
            is_active=False
        )
        try:
            email = send_verification_email(user)
            email.content_subtype = "html"  # Set content type to HTML
            email.send()
        except Exception as e:
            print("Exp-----------",e)
        print("Activation email sent to:", user)
        
        # Serialize user data
        serialize = UserSerializerWithToken(user, many=False).data
        return Response(serialize, status=status.HTTP_200_OK)
    
    except KeyError as e:
        message = {'details': f"Missing field: {str(e)}"}
        return Response(message, status=status.HTTP_400_BAD_REQUEST)
    
    except DRFValidationError as e:
        # Handle field-specific validation errors
        return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
    
    except ValidationError as e:
        # Handle Django model validation errors
        message = {'details': str(e)}
        return Response(message, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        # Catch-all for any other exceptions
        message = {'details': f"User Already exist with this Email ID:{email}"}
        print(e)
        return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(["GET"])
def activateAccount(request, uidb64, token):
    """
    Activates a user's account upon verifying a token from an email link.
    Parameters:
    - request: The HTTP GET request object.
    - uidb64 (str): Base64 encoded user ID to identify the user in the database.
    - token (str): JWT token that contains user-specific data for verification, including an expiration timestamp.

    Returns:
    - JSON response with details of the outcome:
      - "Account activated successfully!" if token is valid and account is activated.
      - "Verification link has expired. New verification link sent." if the token is expired.
      - "Invalid token!" if the token is invalid or doesn't match the user.

    Usage:
    - Include this function as a URL endpoint in your Django application.
    - Users receive a verification email containing a link with `uidb64` and `token` as parameters.
    - On clicking the link, they are redirected to this endpoint for account verification.

    Raises:
    - jwt.ExpiredSignatureError: If the token has expired.
    - jwt.InvalidTokenError: If the token is invalid.
    - Exception: Any other unexpected errors.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = MyUserTable.objects.get(id=uid)  # Adjust this line based on your model
        
        # Decode the token to get user ID and expiration time
        decoded_payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        
        if decoded_payload['user_id'] != user.id:
            return Response({'details': 'Invalid token!'}, status=status.HTTP_400_BAD_REQUEST)
        
        current_time = datetime.now(timezone.utc)
        expiration_time = datetime.fromtimestamp(decoded_payload['exp'], tz=timezone.utc)

        # Check if the token has expired
        if current_time > expiration_time:
            email = send_verification_email(user)
            email.content_subtype = "html"  # Set content type to HTML
            email.send()
            return Response({'details': 'Verification link has expired. New Verification Link send'}, status=status.HTTP_400_BAD_REQUEST)

        # Activate the user account
        user.is_active = True
        user.save()
        return Response({'details': 'Account activated successfully!'}, status=status.HTTP_200_OK)

    except jwt.ExpiredSignatureError:
        email = send_verification_email(user)
        email.content_subtype = "html"
        email.send()
        return Response({'details': 'Verification link has expired. New Verification Link send'}, status=status.HTTP_400_BAD_REQUEST)
    except jwt.InvalidTokenError:
        return Response({'details': 'Invalid token!'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'details': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
#-----------------------------------------------------------------------------
#               File Access API
#-----------------------------------------------------------------------------
import os
from rest_framework.views import APIView


class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        """
        Handle file upload from authenticated users.

        Args:
            request: The HTTP request object containing the file data.

        Returns:
            Response: A Response object containing the serializer data or error messages.
        """
        serializer = FileUploadSerializer(data=request.data)

        # Check if the received data is valid
        if serializer.is_valid():
            file_upload = serializer.save()  # Save file and other data to the model
            FilePermission.objects.create(user=request.user, file=file_upload)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # If not valid, return error details
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def protected_media(request, path):
    """
    Serve files from the media directory for authenticated users only.
    
    Args:
        request: The HTTP request object.
        path: The relative path to the file within the media directory.

    Returns:
        HTTP response containing the requested file or an error message.
    """
    media_root = os.path.join(settings.MEDIA_ROOT)  # Use Django's media root setting
    file_path = os.path.join(media_root, path)
    # Check if the file exists and the user has permission
    if os.path.exists(file_path):
        try:    
            file_upload = FileUpload.objects.get(file=path)
            if FilePermission.objects.filter(user=request.user, file=file_upload).exists():
                with open(file_path, 'rb') as file:
                    response = HttpResponse(file.read(), content_type="application/pdf")
                    response['Content-Disposition'] = f'inline; filename={os.path.basename(file_path)}'
                    return response
            return Response({"message":"File not Found"},status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print("Exception---",e)
            return Response({"message":"You don't have permission to accesss file"},status=status.HTTP_401_UNAUTHORIZED)
    else:
        return Response({"message":"File not Found"},status=status.HTTP_404_NOT_FOUND)

