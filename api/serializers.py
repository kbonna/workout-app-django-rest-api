from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings

from .models import Exercise, Muscle, Tag, YoutubeLink
from .validators import youtube_link, only_letters_and_numbers


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name']
        extra_kwargs = {'name': {'validators': [only_letters_and_numbers]}}


class YoutubeLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = YoutubeLink
        fields = ['url']
        extra_kwargs = {'url': {'validators': [youtube_link]}}


class MuscleSerialzier(serializers.ModelSerializer):
    class Meta:
        model = Muscle
        fields = ['name']
        extra_kwargs = {'name': {'validators': []}}


class ExerciseListSerializer(serializers.ModelSerializer):
    '''Brief exercise data meant to be displayed on the list of exercises.'''

    kind_display = serializers.CharField(
        source='get_kind_display', read_only=True
    )
    can_be_forked = serializers.SerializerMethodField(
        '_can_be_forked', read_only=True
    )

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

    tags = serializers.StringRelatedField(many=True, read_only=True)
    muscles = serializers.StringRelatedField(many=True, read_only=True)
    tutorials = serializers.StringRelatedField(many=True, read_only=True)
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


class ExerciseCreateSerializer(serializers.ModelSerializer):
    '''Create exercise for specific user and save it to db.'''

    tags = TagSerializer(many=True)
    tutorials = YoutubeLinkSerializer(many=True)
    muscles = MuscleSerialzier(many=True)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        tutorials = validated_data.pop('tutorials')
        muscles = validated_data.pop('muscles')

        instance = Exercise(**validated_data)
        instance.save()

        for tag_data in tags:
            instance.tags.add(Tag.objects.get_or_create(**tag_data)[0])
        for tutorial_data in tutorials:
            instance.tutorials.add(
                YoutubeLink.objects.get_or_create(**tutorial_data)[0]
            )
        for muscle_data in muscles:
            instance.muscles.add(Muscle.objects.get(name=muscle_data['name']))

        return instance

    class Meta:
        model = Exercise
        fields = (
            "name",
            "kind",
            "instructions",
            "owner",
            "tags",
            "tutorials",
            "muscles",
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
