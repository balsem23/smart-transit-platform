from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit_tracking', '0004_trip_last_gps'),
    ]

    operations = [
        migrations.AddField(
            model_name='station',
            name='gtfs_stop_id',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='route',
            name='gtfs_route_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='trip',
            name='gtfs_trip_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
