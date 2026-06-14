from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('transit_tracking', '0005_gtfs_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='Trajet',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'trajets',
            },
        ),
        migrations.CreateModel(
            name='TrajetStation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('order', models.PositiveIntegerField()),
                ('time_to_next_station', models.PositiveIntegerField(help_text='Minutes from this station to the next')),
                ('trajet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trajet_stations', to='transit_tracking.trajet')),
                ('station', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='transit_tracking.station')),
            ],
            options={
                'db_table': 'trajet_stations',
                'ordering': ['order'],
                'unique_together': {('trajet', 'station'), ('trajet', 'order')},
            },
        ),
        migrations.CreateModel(
            name='DriverActiveTrajet',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('driver_id', models.UUIDField()),
                ('current_order', models.PositiveIntegerField()),
                ('status', models.CharField(choices=[('NOT_STARTED', 'Not Started'), ('IN_PROGRESS', 'In Progress'), ('ARRIVED_AT_STATION', 'Arrived at Station'), ('FINISHED', 'Finished'), ('CANCELLED', 'Cancelled')], default='NOT_STARTED', max_length=20)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('finished_at', models.DateTimeField(blank=True, null=True)),
                ('arrival_station', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='active_trajets_arrived', to='transit_tracking.station')),
                ('current_station', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='active_trajets_current', to='transit_tracking.station')),
                ('departure_station', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='active_trajets_departed', to='transit_tracking.station')),
                ('trajet', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='transit_tracking.trajet')),
                ('vehicle', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, to='transit_tracking.vehicle')),
            ],
            options={
                'db_table': 'driver_active_trajets',
            },
        ),
    ]
