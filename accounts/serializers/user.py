from django.contrib.auth.models import User
from rest_framework import serializers

from ..models import UserProfile


class UserSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True, min_length=4)

    class Meta:
        model = User
        fields = ("pk", "username", "email", "password")

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance


class UserProfileSerializer(serializers.ModelSerializer):
    gender_display = serializers.CharField(source="get_gender_display", read_only=True)

    class Meta:
        model = UserProfile
        fields = ("country", "city", "profile_picture", "gender", "gender_display", "date_of_birth")
        extra_kwargs = {
            "date_of_birth": {"format": r"%Y-%m-%d", "input_formats": [r"%Y-%m-%d", "iso-8601"]}
        }


class BasicUserDetailSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()

    class Meta:
        model = User
        fields = ("pk", "username", "first_name", "last_name", "last_login", "profile")
        read_only_fields = ("pk", "username", "first_name", "last_name", "last_login", "profile")
        depth = 1


class FullUserDetailSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=True)

    class Meta:
        model = User
        fields = ("pk", "username", "first_name", "last_name", "last_login", "email", "profile")
        read_only_fields = ("username", "email", "last_login")
        depth = 1

    def update(self, instance, validated_data):
        # Update User fields
        instance.first_name = validated_data.get("first_name")
        instance.last_name = validated_data.get("last_name")
        instance.instructions = validated_data.get("instructions")

        # Update UserProfile fields
        instance.profile.country = validated_data.get("profile").get("country", "")
        instance.profile.city = validated_data.get("profile").get("city", "")
        instance.profile.gender = validated_data.get("profile").get("gender", "")
        instance.profile.date_of_birth = validated_data.get("profile").get("date_of_birth", None)

        instance.save()
        return instance


class UserProfilePictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ("profile_picture",)
        extra_kwargs = {
            "profile_picture": {"allow_empty_file": False, "use_url": True, "required": True}
        }


class UserPasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=4, required=True)

    class Meta:
        model = User
        fields = ("password",)

    def update(self, instance, validated_data):
        password = validated_data.pop("password")
        instance.set_password(password)
        instance.save()
        return instance


class UserEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("email",)
        extra_kwargs = {"email": {"required": True}}
