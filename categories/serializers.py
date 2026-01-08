from rest_framework import serializers
from .models import Category

class CategorySerializer(serializers.ModelSerializer):
    categoryName = serializers.CharField(min_length=2, max_length=50)
    class Meta:
        model = Category
        fields = ['id', 'categoryName', 'description']
