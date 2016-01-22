from django.contrib.auth.models import User, Group
from rest_framework import serializers
from .models import recommendations

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


class RecSerializer(serializers.Serializer):
    class Meta:
        model = recommendations
        fields = ('row', 'cell')
    row = serializers.CharField(max_length=2)
    cell = serializers.CharField(max_length=2)

class recommendationsSerializer(serializers.Serializer):
    class Meta:
        model = recommendations
        fields = ('row', 'cell')
