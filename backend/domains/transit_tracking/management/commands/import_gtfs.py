import io
import zipfile
from django.core.management.base import BaseCommand
from domains.transit_tracking.utils import parse_and_import_gtfs

TRANSTU_GTFS_URL = (
    'https://catalogue-data.transport.tn/dataset/fe6c29b8-86c8-44cd-b36d-d41b70fab3f2/'
    'resource/841146b3-8dc9-4b23-88f2-880d64a50f34/download/'
    'fe6c29b8-86c8-44cd-b36d-d41b70fab3f2_41e5bb3e-3ef6-4d1e-ba29-e504601ab17b.zip'
)


class Command(BaseCommand):
    help = 'Télécharge et importe les données GTFS TRANSTU'

    def handle(self, *args, **options):
        self.stdout.write('Téléchargement du fichier GTFS TRANSTU...')
        try:
            import requests
            resp = requests.get(TRANSTU_GTFS_URL, timeout=120)
            resp.raise_for_status()
        except Exception as e:
            self.stderr.write(f'Erreur de téléchargement: {e}')
            return

        self.stdout.write('Importation des données...')
        try:
            zf = zipfile.ZipFile(io.BytesIO(resp.content))
            created = parse_and_import_gtfs(zf)
        except Exception as e:
            self.stderr.write(f'Erreur d\'importation: {e}')
            return

        self.stdout.write(self.style.SUCCESS(
            f'Importation réussie: {created["stations"]} stations, '
            f'{created["routes"]} routes, {created["route_stations"]} arrêts ordonnés.'
        ))
