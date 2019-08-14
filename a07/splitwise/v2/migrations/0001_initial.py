# Generated by Django 2.2.4 on 2019-08-09 08:52

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Categories',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Expenses',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=1000)),
                ('deleted', models.BooleanField(default=False)),
                ('total_amount', models.FloatField()),
                ('categories', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='v2.Categories')),
            ],
        ),
        migrations.CreateModel(
            name='ExpenseInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('owe', models.FloatField()),
                ('lend', models.FloatField()),
                ('expense', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='v2.Expenses')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
