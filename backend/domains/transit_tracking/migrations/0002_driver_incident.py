import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit_tracking', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DriverIncident',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('driver_id', models.UUIDField()),
                ('type', models.CharField(choices=[('DELAY', 'Delay'), ('BREAKDOWN', 'Breakdown'), ('ACCIDENT', 'Accident'), ('SECURITY', 'Security'), ('OTHER', 'Other')], default='OTHER', max_length=20)),
                ('description', models.TextField()),
                ('location_lat', models.FloatField(blank=True, null=True)),
                ('location_lng', models.FloatField(blank=True, null=True)),
                ('status', models.CharField(default='OPEN', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('trip', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='transit_tracking.trip')),
            ],
            options={
                'db_table': 'driver_incidents',
            },
        ),
    ]
