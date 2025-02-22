# Generated by Django 4.1.5 on 2023-03-11 21:15

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0014_alter_heartratedata_heart_rate'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='heartratedata',
            options={},
        ),
        migrations.AddField(
            model_name='heartratedata',
            name='end_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='heartratedata',
            name='start_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='runningworkoutdata',
            name='heart_rate_data',
            field=models.ManyToManyField(blank=True, to='application.heartratedata'),
        ),
        migrations.AlterField(
            model_name='heartratedata',
            name='heart_rate',
            field=models.FloatField(default=0),
        ),
    ]
