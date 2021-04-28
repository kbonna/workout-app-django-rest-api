from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator, ValidationError

from api.models import Exercise, Tag, Muscle, YoutubeLink
from api.serializers.muscle import MuscleSerializer
from api.serializers.tag import TagSerializer
from api.serializers.youtube_link import YoutubeLinkSerializer


class ExerciseSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    tutorials = YoutubeLinkSerializer(many=True)
    muscles = MuscleSerializer(many=True)
    owner_username = serializers.CharField(source="owner.username", read_only=True)
    kind_display = serializers.CharField(source="get_kind_display", read_only=True)
    can_be_forked = serializers.SerializerMethodField("_can_be_forked", read_only=True)

    def _can_be_forked(self, obj):
        request = self.context.get("request")
        if request is not None:
            return obj.can_be_forked(request.user.pk)
        return None

    def validate(self, data):
        requesting_user = self.context["request"].user
        if Exercise.objects.filter(owner=requesting_user, name=data["name"]).exists():
            raise ValidationError({"name": "You already own this exercise."})
        return data

    def create(self, validated_data):
        tags = validated_data.pop("tags")
        tutorials = validated_data.pop("tutorials")
        muscles = validated_data.pop("muscles")

        instance = Exercise(**validated_data, owner=self.context["request"].user)
        instance.save()

        for tag_data in tags:
            instance.tags.add(Tag.objects.get_or_create(**tag_data)[0])
        for tutorial_data in tutorials:
            instance.tutorials.add(YoutubeLink.objects.get_or_create(**tutorial_data)[0])
        for muscle_data in muscles:
            instance.muscles.add(Muscle.objects.get(**muscle_data))

        return instance

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name")
        instance.kind = validated_data.get("kind")
        instance.instructions = validated_data.get("instructions")

        # Update many-to-many relations
        new_tags = [
            Tag.objects.get_or_create(**tag_data)[0] for tag_data in validated_data.get("tags")
        ]
        new_tutorials = [
            YoutubeLink.objects.get_or_create(**tutorial_data)[0]
            for tutorial_data in validated_data.get("tutorials")
        ]
        new_muscles = [
            Muscle.objects.get(**muscle_data) for muscle_data in validated_data.get("muscles")
        ]
        instance.tags.set(new_tags)
        instance.tutorials.set(new_tutorials)
        instance.muscles.set(new_muscles)

        instance.save()

        return instance

    class Meta:
        model = Exercise
        fields = (
            "pk",
            "name",
            "kind",
            "kind_display",
            "owner",
            "owner_username",
            "can_be_forked",
            "forks_count",
            "tags",
            "muscles",
            "tutorials",
            "instructions",
        )
        extra_kwargs = {"owner": {"read_only": True}}
