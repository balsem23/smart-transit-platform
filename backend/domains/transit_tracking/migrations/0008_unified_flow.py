from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('transit_tracking', '0007_google_station_import'),
    ]

    operations = [
        migrations.AddField(
            model_name='routestation',
            name='time_to_next_station',
            field=models.PositiveIntegerField(default=5, help_text='Minutes from this station to the next'),
        ),
        migrations.CreateModel(
            name='DriverSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('driver_id', models.UUIDField()),
                ('current_order', models.PositiveIntegerField()),
                ('status', models.CharField(choices=[('IN_PROGRESS', 'In Progress'), ('ARRIVED_AT_STATION', 'Arrived at Station'), ('FINISHED', 'Finished'), ('CANCELLED', 'Cancelled')], default='IN_PROGRESS', max_length=20)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('finished_at', models.DateTimeField(blank=True, null=True)),
                ('arrival_station', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='sessions_arrived', to='transit_tracking.station')),
                ('current_station', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='sessions_current', to='transit_tracking.station')),
                ('departure_station', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='sessions_departed', to='transit_tracking.station')),
                ('route', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='transit_tracking.route')),
                ('vehicle', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, to='transit_tracking.vehicle')),
            ],
            options={
                'db_table': 'driver_sessions',
            },
        ),
        migrations.DeleteModel(
            name='DriverActiveTrajet',
        ),
        migrations.DeleteModel(
            name='TrajetStation',
        ),
        migrations.DeleteModel(
            name='Trajet',
        ),
    ]
