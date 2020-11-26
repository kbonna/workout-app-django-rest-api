from rest_framework import serializers

from ..models import Exercise, Tag, Muscle, YoutubeLink
from api.serializers.muscle import MuscleSerializer
from api.serializers.tag import TagSerializer
from api.serializers.youtube_link import YoutubeLinkSerializer


class ExerciseSerializer(serializers.ModelSerializer):
    '''...'''

    tags = TagSerializer(many=True)
    tutorials = YoutubeLinkSerializer(many=True)
    muscles = MuscleSerializer(many=True)
    owner_username = serializers.CharField(
        source='owner.username', read_only=True
    )
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
            'pk',
            'name',
            'kind',
            'kind_display',
            'owner',
            'owner_username',
            'can_be_forked',
            'forks_count',
            'tags',
            'muscles',
            'tutorials',
            'instructions',
        )


# class ExerciseCreateSerializer(serializers.ModelSerializer):
#     '''Create exercise for specific user and save it to db.'''

#     tags = TagSerializer(many=True)
#     tutorials = YoutubeLinkSerializer(many=True)
#     muscles = MuscleSerializer(many=True)

#     def create(self, validated_data):
#         tags = validated_data.pop('tags')
#         tutorials = validated_data.pop('tutorials')
#         muscles = validated_data.pop('muscles')

#         instance = Exercise(**validated_data)
#         instance.save()

#         for tag_data in tags:
#             instance.tags.add(Tag.objects.get_or_create(**tag_data)[0])
#         for tutorial_data in tutorials:
#             instance.tutorials.add(
#                 YoutubeLink.objects.get_or_create(**tutorial_data)[0]
#             )
#         for muscle_data in muscles:
#             instance.muscles.add(Muscle.objects.get(name=muscle_data['name']))

#         return instance

#     class Meta:
#         model = Exercise
#         fields = (
#             "name",
#             "kind",
#             "instructions",
#             "owner",
#             "tags",
#             "tutorials",
#             "muscles",
#         )
