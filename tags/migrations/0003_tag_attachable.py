# Generated by Django 3.0.4 on 2020-04-08 10:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0002_tag_user_set'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='attachable',
            field=models.BooleanField(default=True),
        ),
    ]
