# Generated by Django 5.1.6 on 2025-03-04 15:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('serviceApp', '0006_alter_review_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='service',
            name='duration',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
    ]
