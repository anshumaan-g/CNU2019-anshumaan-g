from rest_framework import serializers
from v2.models import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'password')


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expenses
        fields = ('description', 'categories', 'total_amount')


class ExpenseUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseInfo
        fields = ('user', 'owe', 'lend', 'expense')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = ('name',)


class UpdateExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expenses
        fields = ()
