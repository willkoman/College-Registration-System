# Generated by Django 4.2.5 on 2023-12-05 19:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0013_alter_faculty_parttime_num_of_courses_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='user_type',
            field=models.CharField(choices=[('Admin', 'Admin'), ('Student', 'Student'), ('Faculty', 'Faculty'), ('Statistics', 'Statistics')], max_length=10),
        ),
    ]