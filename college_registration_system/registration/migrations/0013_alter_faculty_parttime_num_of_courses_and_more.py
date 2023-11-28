# Generated by Django 4.2.5 on 2023-11-28 01:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0012_alter_faculty_fulltime_num_of_courses'),
    ]

    operations = [
        migrations.AlterField(
            model_name='faculty_parttime',
            name='num_of_courses',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='undergrad_full_time',
            name='max_creds',
            field=models.IntegerField(default=16),
        ),
        migrations.AlterField(
            model_name='undergrad_full_time',
            name='min_creds',
            field=models.IntegerField(default=9),
        ),
        migrations.AlterField(
            model_name='undergrad_part_time',
            name='max_creds',
            field=models.IntegerField(default=8),
        ),
        migrations.AlterField(
            model_name='undergrad_part_time',
            name='min_creds',
            field=models.IntegerField(default=3),
        ),
    ]
