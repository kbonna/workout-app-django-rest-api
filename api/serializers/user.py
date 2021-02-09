from api.models import UserProfile
from django.contrib.auth.models import User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True, min_length=4)

    class Meta:
        model = User
        fields = ("pk", "username", "password")

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ("country", "city", "profile_picture")
        read_only_fields = ("profile_picture",)


class UserProfilePictureSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(max_length=100, allow_empty_file=False, required=True)

    class Meta:
        model = UserProfile
        fields = ("profile_picture",)

    def update(self, instance, validated_data):
        instance.profile_picture = validated_data.get("profile_picture")
        instance.save()
        return instance


class UserDetailSerializer(serializers.ModelSerializer):

    profile = UserProfileSerializer(required=True)

    class Meta:
        model = User
        fields = ("pk", "username", "first_name", "last_name", "email", "profile")
        read_only_fields = ("username", "email")
        depth = 1

    def update(self, instance, validated_data):
        # Update User fields
        instance.first_name = validated_data.get("first_name")
        instance.last_name = validated_data.get("last_name")
        instance.instructions = validated_data.get("instructions")

        # Update UserProfile fields
        instance.profile.country = validated_data.get("profile").get("country", "")
        instance.profile.city = validated_data.get("profile").get("city", "")

        instance.save()
        return instance
