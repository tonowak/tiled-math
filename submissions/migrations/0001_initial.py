# Generated by Django 3.0.5 on 2020-04-29 18:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('folder', '0004_auto_20200407_2032'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('problems', '0007_auto_20200415_1155'),
        ('files', '0002_savedimage_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='Thread',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_public', models.BooleanField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('parent_folder', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='folder.Folder')),
                ('parent_problem', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='problems.Problem')),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('description', models.TextField()),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('thread', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='submissions.Thread')),
            ],
        ),
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='submissions.Comment')),
                ('image', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='files.SavedImage')),
            ],
        ),
    ]
