# Generated by Django 5.0.6 on 2024-06-30 10:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_messaging', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatthread',
            name='primary_last_message_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
