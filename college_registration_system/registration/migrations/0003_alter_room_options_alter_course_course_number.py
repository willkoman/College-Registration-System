# Generated by Django 4.2.5 on 2023-10-16 17:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0002_rename_student_year_student_enrollment_year'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='room',
            options={'ordering': ['room_no']},
        ),
        migrations.AlterField(
            model_name='course',
            name='course_number',
            field=models.IntegerField(),
        ),
    ]