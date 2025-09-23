from django.contrib.auth.models import User
from rest_framework import serializers, validators
from .models import Profile
from .models import SwapSession
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Profile, SwapSession
from .models import Rating

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        validators=[validators.UniqueValidator(User.objects.all(), "A user with that email already exists.")]
    )
    full_name = serializers.CharField(required=True, max_length=100)
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        fields = ('full_name', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"]
        )
        return user

class EmailLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'skills_offered', 'skills_wanted', 'available_hours', 'user', 'average_rating', 'rating_count']
        read_only_fields = ['user', 'average_rating', 'rating_count']

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name']

class SwapSessionSerializer(serializers.ModelSerializer):
    proposer = UserSerializer(read_only=True)
    #receiver = UserSerializer(read_only=True)

    class Meta:
        model = SwapSession
        fields = '__all__'


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        return token

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            try:
                user = User.objects.get(email=email)
                if user.check_password(password):
                    attrs['username'] = user.username
                    del attrs['email']
                else:
                    raise serializers.ValidationError("Incorrect credentials")
            except User.DoesNotExist:
                raise serializers.ValidationError("Incorrect credentials")
        else:
            raise serializers.ValidationError("Must include 'email' and 'password'")

        return super().validate(attrs)

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['score',]