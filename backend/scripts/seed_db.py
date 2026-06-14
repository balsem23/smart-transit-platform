import os
import sys
import django
from pathlib import Path

# Setup Django environment
sys.path.append(str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.db import transaction
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from domains.auth_identity.models import User
from domains.transit_tracking.models import Line, Trajet, TrajetStation, Station, Trip, Vehicle
from domains.wallet_payments.models import Wallet

@transaction.atomic
def run_seeders():
    """
    DÉCISION CTO : Script d'amorçage "Idempotent".
    Peut être lancé plusieurs fois sans casser l'intégrité de la DB.
    Idéal pour l'onboarding de développeurs sur la stack locale.
    """
    print("🚀 Démarrage du Seeding de la base de données (transport_db)...")

    # 1. Création Admin
    admin_phone = "+21650000000"
    if not User.objects.filter(phone_number=admin_phone).exists():
        User.objects.create(
            phone_number=admin_phone,
            password=make_password("AdminSecure123!"),
            role="SUPER_ADMIN"
        )
        print(f"✅ Administrateur créé : {admin_phone}")
        
    # 2. Création Controller
    controller_phone = "+21670000000"
    if not User.objects.filter(phone_number=controller_phone).exists():
        User.objects.create(
            phone_number=controller_phone,
            password=make_password("Controller123!"),
            role="CONTROLLER"
        )
        print(f"✅ Contrôleur créé : {controller_phone}")

    # 3. Création Passenger
    test_phone = "+21699000000"
    if not User.objects.filter(phone_number=test_phone).exists():
        passenger = User.objects.create(
            phone_number=test_phone,
            password=make_password("Passenger123!"),
            role="PASSENGER"
        )
        Wallet.objects.create(passenger=passenger, balance=50.000)
        print(f"✅ Passager créé avec 50 TND : {test_phone}")

    # 4. Création Driver
    driver_phone = "+21620000000"
    driver = None
    if not User.objects.filter(phone_number=driver_phone).exists():
        driver = User.objects.create(
            phone_number=driver_phone,
            password=make_password("Driver123!"),
            role="DRIVER",
            first_name="Conducteur",
            last_name="Test",
            email="driver@sitp.tn",
        )
        print(f"✅ Chauffeur créé : {driver_phone}")
    else:
        driver = User.objects.get(phone_number=driver_phone)
        driver.first_name = driver.first_name or "Conducteur"
        driver.last_name = driver.last_name or "Test"
        driver.email = driver.email or "driver@sitp.tn"
        driver.save(update_fields=["first_name", "last_name", "email"])

    # 5. Création Géographique locale
    if not Line.objects.exists():
        line = Line.objects.create(name="TGM", color_code="#0000FF")
        station_a = Station.objects.create(name="Tunis Marine", location_lat=36.8065, location_lng=10.1815, has_kiosk=True)
        station_b = Station.objects.create(name="Carthage", location_lat=36.8528, location_lng=10.3233, has_kiosk=True)
        station_c = Station.objects.create(name="Sidi Bou Said", location_lat=36.8702, location_lng=10.3417, has_kiosk=True)
        station_d = Station.objects.create(name="Marsa Plage", location_lat=36.8833, location_lng=10.3293, has_kiosk=True)
        trajet = Trajet.objects.create(
            line=line,
            name="Tunis Marine -> Marsa Plage",
            start_station=station_a,
            end_station=station_d,
            path_coordinates="36.8065,10.1815;36.8528,10.3233;36.8702,10.3417;36.8833,10.3293"
        )
        for order_number, station in enumerate([station_a, station_b, station_c, station_d], start=1):
            TrajetStation.objects.create(trajet=trajet, station=station, order_number=order_number)
        Vehicle.objects.create(plate_number="123-TU-4567", fleet_id="TGM-001", driver_id=driver.id, capacity=300)
        print("✅ Données géographiques locales (Lignes, Routes, Stations) créées.")

    for trajet in Trajet.objects.all():
        if not trajet.trajet_stations.exists():
            stations = list(Station.objects.all().order_by('name'))
            for order_number, station in enumerate(stations, start=1):
                TrajetStation.objects.get_or_create(trajet=trajet, station=station, defaults={'order_number': order_number})
            if stations:
                trajet.start_station = trajet.start_station or stations[0]
                trajet.end_station = trajet.end_station or stations[-1]
                trajet.save(update_fields=['start_station', 'end_station'])

    trajet = Trajet.objects.first()
    vehicle = Vehicle.objects.first()
    if driver and trajet and vehicle and not Trip.objects.filter(driver_id=driver.id).exists():
        trajet_stations = list(trajet.trajet_stations.select_related('station').order_by('order_number'))
        Trip.objects.create(
            trajet=trajet,
            vehicle=vehicle,
            driver_id=driver.id,
            current_station=trajet_stations[0].station if trajet_stations else None,
            destination_station=trajet_stations[-1].station if trajet_stations else None,
            scheduled_start=timezone.now(),
            status="SCHEDULED",
        )
        print("✅ Trajet de test affecté au conducteur.")

    print("🎉 Base de données initialisée avec succès.")

if __name__ == '__main__':
    run_seeders()
