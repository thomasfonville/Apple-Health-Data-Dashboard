# Generated by Django 4.1.5 on 2023-01-31 17:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0004_rename_cals_burned_workoutdata_active_energy_burned'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workoutdata',
            name='active_energy_burned',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='workoutdata',
            name='distance',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='workoutdata',
            name='duration',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='workoutdata',
            name='end_date',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='workoutdata',
            name='source',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='workoutdata',
            name='start_date',
            field=models.CharField(max_length=50),
        ),
    ]
