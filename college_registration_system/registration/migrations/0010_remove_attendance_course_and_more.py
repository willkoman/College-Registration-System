# Generated by Django 4.2.5 on 2023-11-20 15:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0009_alter_faculty_rank'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attendance',
            name='course',
        ),
        migrations.RemoveField(
            model_name='studenthistory',
            name='course',
        ),
    ]