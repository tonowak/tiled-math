# Generated by Django 3.0.5 on 2020-05-06 20:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('folder', '0006_auto_20200506_2236'),
    ]

    operations = [
        migrations.RenameField(
            model_name='folder',
            old_name='tag_set',
            new_name='direct_tag_set',
        ),
    ]
