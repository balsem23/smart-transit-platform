from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit_tracking', '0003_station_based_trips'),
    ]

    operations = [
        migrations.AddField(
            model_name='trip',
            name='last_latitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='trip',
            name='last_longitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='trip',
            name='last_gps_update_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
