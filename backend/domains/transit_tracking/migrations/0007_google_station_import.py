from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit_tracking', '0006_trajet_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='station',
            name='is_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='GoogleStationImport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('formatted_address', models.TextField(blank=True)),
                ('latitude', models.DecimalField(decimal_places=7, max_digits=10)),
                ('longitude', models.DecimalField(decimal_places=7, max_digits=10)),
                ('google_place_id', models.CharField(max_length=255, unique=True)),
                ('type', models.CharField(choices=[('BUS', 'Bus'), ('METRO', 'Metro'), ('TRAIN', 'Train'), ('UNKNOWN', 'Unknown')], default='UNKNOWN', max_length=20)),
                ('city', models.CharField(blank=True, max_length=100)),
                ('is_imported', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Google Station Import',
                'verbose_name_plural': 'Google Station Imports',
                'db_table': 'google_station_imports',
            },
        ),
    ]
