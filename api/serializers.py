from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings

from .models import Exercise, Muscle, Tag, YoutubeLink


class ExerciseListSerializer(serializers.ModelSerializer):
    '''Brief exercise data meant to be displayed on the list of exercises.'''

    kind_display = serializers.CharField(source='get_kind_display')
    can_be_forked = serializers.SerializerMethodField('_can_be_forked')

    def _can_be_forked(self, obj):
        user_id = self.context.get("user_id")
        if user_id is not None:
            return obj.can_be_forked(user_id)
        return None

    class Meta:
        model = Exercise
        fields = (
            'pk',
            'name',
            'kind_display',
            'owner',
            'forks_count',
            'can_be_forked',
        )


class ExerciseDetailSerializer(ExerciseListSerializer):
    '''Detailed exercise data displayed on exercise page.'''

    tags = serializers.StringRelatedField(read_only=True, many=True)
    muscles = serializers.StringRelatedField(read_only=True, many=True)
    tutorials = serializers.StringRelatedField(read_only=True, many=True)
    owner_username = serializers.CharField(
        source='owner.username', read_only=True
    )

    class Meta(ExerciseListSerializer.Meta):
        model = Exercise
        fields = ExerciseListSerializer.Meta.fields + (
            'owner_username',
            'tags',
            'muscles',
            'tutorials',
            'instructions',
        )


class UserSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'pk', 'password')

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance
