from rest_framework import serializers
from .models import Policy, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class PolicyListSerializer(serializers.ModelSerializer):
    """목록용 - 간략한 정보"""
    categories = CategorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Policy
        fields = [
            'plcy_no',
            'plcy_nm',
            'district',
            'aply_end_dt',
            'categories',
        ]


class PolicyDetailSerializer(serializers.ModelSerializer):
    """상세용 - 전체 정보"""
    categories = CategorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Policy
        fields = '__all__'