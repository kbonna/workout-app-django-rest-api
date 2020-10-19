from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings

from .models import Exercise, Muscle, Tag, YoutubeLink


class ExerciseListSerializer(serializers.ModelSerializer):
    '''Brief exercise data meant to be displayed on the list of exercises.'''
    kind_display = serializers.CharField(source='get_kind_display')

    class Meta:
        model = Exercise
        fields = ('pk', 'name', 'kind_display')

class ExerciseDetailSerializer(serializers.ModelSerializer):
    '''Detailed exercise data displayed on exercise page.'''
    tags = serializers.StringRelatedField(read_only=True, many=True)
    muscles = serializers.StringRelatedField(read_only=True, many=True)
    tutorials = serializers.StringRelatedField(read_only=True, many=True)
    kind_display = serializers.CharField(source='get_kind_display')
    owner_username = serializers.SlugRelatedField(
        read_only=True,
        slug_field='owner_username'
        )

    class Meta:
        model = Exercise
        fields = ('pk', 'name', 'kind_display', 'instructions',
                  'owner_username', 'forks_count', 'tags', 'tutorials',
                  'muscles')


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('username', 'pk')


class UserSerializerWithToken(serializers.ModelSerializer):

    token = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True)

    def get_token(self, obj):
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(obj)
        token = jwt_encode_handler(payload)
        return token

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

    class Meta:
        model = User
        fields = ('username', 'pk', 'password', 'token')
