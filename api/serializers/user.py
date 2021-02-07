from django.contrib.auth.models import User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("username", "pk", "password")

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "profile")
        depth = 1
