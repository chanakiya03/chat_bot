from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from .models import CollegeDetail

class CollegeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollegeDetail
        fields = '__all__'

class CollegeSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = CollegeDetail
        fields = ['name', 'slug']

class MessageSerializer(serializers.Serializer):
    message = serializers.CharField()

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(source='date_joined', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'phone', 'password', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate_password(self, value):
        return make_password(value)

    def create(self, validated_data):
        # Username is required by AbstractUser, we use email but must provide username
        if 'username' not in validated_data:
            validated_data['username'] = validated_data['email']
        return super().create(validated_data)
