import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('transit_tracking', '0008_unified_flow'),
    ]

    operations = [
        # Rename Route → Trajet
        migrations.RenameModel('Route', 'Trajet'),
        migrations.AlterModelTable('Trajet', 'trajets'),

        # Rename RouteStation → TrajetStation
        migrations.RenameModel('RouteStation', 'TrajetStation'),
        migrations.AlterModelTable('TrajetStation', 'trajet_stations'),

        # Rename FK field: TrajetStation.route → trajet
        migrations.RenameField('TrajetStation', 'route', 'trajet'),
        # Update related_name on TrajetStation.trajet
        migrations.AlterField(
            model_name='trajetstation',
            name='trajet',
            field=models.ForeignKey('transit_tracking.Trajet', on_delete=models.CASCADE, related_name='trajet_stations'),
        ),

        # Rename FK field: DriverSession.route → trajet
        migrations.RenameField('DriverSession', 'route', 'trajet'),
        # Update related_name on DriverSession.trajet
        migrations.AlterField(
            model_name='driversession',
            name='trajet',
            field=models.ForeignKey('transit_tracking.Trajet', on_delete=models.RESTRICT),
        ),

        # Rename FK field: Trip.route → trajet
        migrations.RenameField('Trip', 'route', 'trajet'),
        # Update related_name on Trip.trajet
        migrations.AlterField(
            model_name='trip',
            name='trajet',
            field=models.ForeignKey('transit_tracking.Trajet', on_delete=models.RESTRICT),
        ),

        # Update related_names on Trajet.start_station and end_station
        migrations.AlterField(
            model_name='trajet',
            name='start_station',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='trajets_starting_here', to='transit_tracking.station'),
        ),
        migrations.AlterField(
            model_name='trajet',
            name='end_station',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='trajets_ending_here', to='transit_tracking.station'),
        ),

        # Remove GoogleStationImport
        migrations.DeleteModel('GoogleStationImport'),

        # Remove old related names in Station that pointed to Route/RouteStation
        # Since we renamed the models, Django handles FK target renames automatically
        # But the related_name for the default reverse accessor still references the old model
        # The reverse relations are: Route.station+ (via start_station/end_station)
        # These were updated above

        # Create ImportedStation
        migrations.CreateModel(
            name='ImportedStation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('formatted_address', models.TextField(blank=True)),
                ('latitude', models.FloatField(blank=True, null=True)),
                ('longitude', models.FloatField(blank=True, null=True)),
                ('source', models.CharField(choices=[('OSM', 'OpenStreetMap'), ('GOOGLE', 'Google Places'), ('GTFS', 'GTFS'), ('MANUAL', 'Manual')], default='OSM', max_length=20)),
                ('external_id', models.CharField(blank=True, db_index=True, max_length=255)),
                ('type', models.CharField(choices=[('BUS', 'Bus'), ('METRO', 'Metro'), ('TRAIN', 'Train'), ('UNKNOWN', 'Unknown')], default='UNKNOWN', max_length=20)),
                ('city', models.CharField(blank=True, max_length=100)),
                ('region', models.CharField(blank=True, max_length=100)),
                ('is_approved', models.BooleanField(default=False)),
                ('approved_station', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='imported_sources', to='transit_tracking.station')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Imported Station',
                'verbose_name_plural': 'Imported Stations',
                'db_table': 'imported_stations',
            },
        ),

        # Create ImportedRoute
        migrations.CreateModel(
            name='ImportedRoute',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('source', models.CharField(choices=[('OSM', 'OpenStreetMap'), ('GOOGLE', 'Google Places'), ('GTFS', 'GTFS'), ('MANUAL', 'Manual')], default='GTFS', max_length=20)),
                ('external_id', models.CharField(blank=True, db_index=True, max_length=255)),
                ('line_name', models.CharField(blank=True, max_length=100)),
                ('is_approved', models.BooleanField(default=False)),
                ('approved_trajet', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='imported_sources', to='transit_tracking.Trajet')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Imported Route',
                'verbose_name_plural': 'Imported Routes',
                'db_table': 'imported_routes',
            },
        ),

        # Create ImportedRouteStation
        migrations.CreateModel(
            name='ImportedRouteStation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('order_number', models.PositiveIntegerField()),
                ('time_to_next_station', models.PositiveIntegerField(default=5, help_text='Minutes from this station to the next')),
                ('imported_route', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='imported_stations', to='transit_tracking.ImportedRoute')),
                ('imported_station', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='transit_tracking.ImportedStation')),
            ],
            options={
                'db_table': 'imported_route_stations',
                'ordering': ['order_number'],
                'unique_together': {('imported_route', 'order_number')},
            },
        ),
    ]
