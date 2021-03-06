from email.utils import parseaddr

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.modules.users.serializers import UserSerializer
from api.modules.users.validators import validate_password, validate_email


@api_view(['POST'])
@permission_classes((AllowAny,))
def sign_up(request):
    """
    Adds a new user to database
    Note: client's email is stored as username in database (NO explicit difference in email and username)
    :param request: contains first name, last name, email Id (username) and password
    :return: 400 if incorrect parameters are sent or email ID already exists
    :return: 201 successful
    """
    firstname = request.POST.get('firstname', None)
    lastname = request.POST.get('lastname', None)
    username = parseaddr(request.POST.get('email', None))[1].lower()
    password = request.POST.get('password', None)

    if not firstname or not lastname or not username or not password:
        # incorrect request received
        error_message = "Missing parameters in request. Send firstname, lastname, email, password"
        return Response(error_message, status=status.HTTP_400_BAD_REQUEST)

    if not validate_email(username):
        error_message = "Invalid email Id"
        return Response(error_message, status=status.HTTP_400_BAD_REQUEST)

    if not validate_password(password):
        error_message = "Invalid Password"
        return Response(error_message, status=status.HTTP_400_BAD_REQUEST)

    try:
        User.objects.get(username=username)
        error_message = "Email Id already exists"
        return Response(error_message, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        user = User.objects.create_user(username, password=password)
        user.first_name = firstname
        user.last_name = lastname
        user.is_superuser = False
        user.is_staff = False
        user.save()
    except Exception as e:
        error_message = str(e)
        return Response(error_message, status=status.HTTP_400_BAD_REQUEST)

    success_message = "Successfully registered"
    return Response(success_message, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def get_user_profile(request):
    """
    Returns user object using user email address
    :param request:
    :param email:
    :return: 200 successful
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['GET'])
def get_users_by_email(request, email):
    """
    Returns user object using user email address
    :param request:
    :param email:
    :return: 200 successful
    """
    users = User.objects.filter(is_staff=False, is_superuser=False, username__startswith=email)[:5]
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def get_user_by_id(request, user_id):
    """
    Returns user object using user id
    :param request:
    :param user_id:
    :return: 400 if incorrect user ID is sent
    :return: 200 successful
    """
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        error_message = "Invalid user ID"
        return Response(error_message, status=status.HTTP_400_BAD_REQUEST)
    serializer = UserSerializer(user)
    return Response(serializer.data)


@api_view(['POST'])
def update_profile_image(request):
    """
    Add a profile image for user
    :param request: contain profile_image_url
    :return: 400 if incorrect parameters are sent
    :return: 201 successful
    """
    profile_image_url = request.POST.get('profile_image_url')
    if not profile_image_url:
        # incorrect request received
        error_message = "Missing parameters in request. Send profile_image_url"
        return Response(error_message, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    if not hasattr(user, 'profile'):
        user.save()  # to handle RelatedObjectDoenNotExist exception on existing users
    user.profile.profile_image = profile_image_url
    user.save()
    return Response(None, status=status.HTTP_200_OK)
