import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit_tracking', '0002_driver_incident'),
    ]

    operations = [
        migrations.AddField(
            model_name='route',
            name='start_station',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='routes_starting_here', to='transit_tracking.station'),
        ),
        migrations.AddField(
            model_name='route',
            name='end_station',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='routes_ending_here', to='transit_tracking.station'),
        ),
        migrations.AddField(
            model_name='vehicle',
            name='driver_id',
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='trip',
            name='current_station',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='trips_currently_here', to='transit_tracking.station'),
        ),
        migrations.AddField(
            model_name='trip',
            name='destination_station',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='trips_destined_here', to='transit_tracking.station'),
        ),
        migrations.CreateModel(
            name='RouteStation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('order_number', models.PositiveIntegerField()),
                ('route', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='route_stations', to='transit_tracking.route')),
                ('station', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='transit_tracking.station')),
            ],
            options={
                'db_table': 'route_stations',
                'ordering': ['order_number'],
                'unique_together': {('route', 'station'), ('route', 'order_number')},
            },
        ),
    ]
