# Generated by Django 5.0.6 on 2024-06-08 10:14

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatThread',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('primary_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chat_primary_user', to=settings.AUTH_USER_MODEL)),
                ('secondary_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chat_secondary_user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('primary_user', 'secondary_user')},
            },
        ),
        migrations.CreateModel(
            name='Chatmessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('message_time', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('thread', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chatmessage_thread', to='core_messaging.chatthread')),
            ],
            options={
                'ordering': ['message_time'],
            },
        ),
    ]
