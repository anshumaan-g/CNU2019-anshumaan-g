from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator


# Create your models here.
class Categories(models.Model):
    name = models.CharField(max_length=100, null=False)

    def __str__(self):
        return self


class Expenses(models.Model):
    description = models.CharField(max_length=1000, null=False)
    deleted = models.BooleanField(default=False)
    categories = models.ForeignKey(Categories, on_delete=models.CASCADE)
    total_amount = models.FloatField(null=False, validators=[MinValueValidator(0.0)])
    time_stamp = models.DateTimeField()

    def __str__(self):
        return self


class ExpenseInfo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    expense = models.ForeignKey(Expenses, on_delete=models.CASCADE)
    owe = models.FloatField(null=False, validators=[MinValueValidator(0.0)])
    lend = models.FloatField(null=False, validators=[MinValueValidator(0.0)])

    def __str(self):
        return self
