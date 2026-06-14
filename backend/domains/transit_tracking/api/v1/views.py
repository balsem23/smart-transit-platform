import io
import zipfile
from math import atan2, cos, radians, sin, sqrt
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework.views import APIView
from .serializers import (BusSearchResultSerializer, DriverIncidentCreateSerializer, DriverIncidentSerializer, DriverSessionSerializer, DriverTripStartSerializer, GPSLogSerializer, GPSUpdateSerializer, ImportedRouteSerializer, ImportedRouteStationSerializer, ImportedStationSerializer, LineSerializer, PromoteRouteSerializer, PromoteStationSerializer, TrajetAdminSerializer, TrajetSerializer, TrajetStationAdminSerializer, TrajetStationSerializer, TrajetWithStationsSerializer, StartJourneySerializer, StationWithETA, TripSerializer, UpdateStationSerializer, VehicleSerializer)
from core.permissions import IsAdmin, IsDriver
from domains.transit_tracking.models import DriverIncident, DriverSession, GPSLog, ImportedRoute, ImportedRouteStation, ImportedStation, Line, Trajet, TrajetStation, Station, Trip, Vehicle
from domains.transit_tracking.services.google_places import fetch_and_store_stations
from domains.transit_tracking.utils import parse_and_import_gtfs


def distance_meters(lat1, lng1, lat2, lng2):
    earth_radius = 6371000
    d_lat = radians(lat2 - lat1)
    d_lng = radians(lng2 - lng1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lng / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return earth_radius * c


def get_next_trajet_station(trip):
    if not trip.current_station:
        return None
    current_ts = TrajetStation.objects.filter(trajet=trip.trajet, station=trip.current_station).first()
    if not current_ts:
        return None
    return TrajetStation.objects.filter(trajet=trip.trajet, order_number__gt=current_ts.order_number).order_by('order_number').first()


def move_trip_to_next_station(trip):
    next_ts = get_next_trajet_station(trip)
    if not next_ts:
        trip.status = 'COMPLETED'
        trip.actual_end = timezone.now()
        trip.save(update_fields=['status', 'actual_end'])
        return trip

    trip.current_station = next_ts.station
    update_fields = ['current_station']
    if trip.destination_station_id == next_ts.station_id:
        trip.status = 'COMPLETED'
        trip.actual_end = timezone.now()
        update_fields.extend(['status', 'actual_end'])
    trip.save(update_fields=update_fields)
    return trip


def get_station_order(trajet_id, station_id):
    ts = TrajetStation.objects.filter(trajet_id=trajet_id, station_id=station_id).first()
    return ts.order_number if ts else None


def get_trajet_stations_between(trajet_id, from_order, to_order):
    return list(TrajetStation.objects.filter(
        trajet_id=trajet_id, order_number__gte=from_order, order_number__lte=to_order
    ).select_related('station').order_by('order_number'))


def calculate_eta(stations, from_index):
    return sum(ts.time_to_next_station for ts in stations[from_index:-1])


class TrajetListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        trajets = Trajet.objects.filter(is_active=True)
        return Response(TrajetSerializer(trajets, many=True).data)


class TripListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        trips = Trip.objects.filter(status='IN_PROGRESS').select_related('trajet', 'vehicle')
        return Response(TripSerializer(trips, many=True).data)


class PassengerLiveTripsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        trips = Trip.objects.filter(status__in=['IN_PROGRESS', 'COMPLETED']).select_related(
            'trajet', 'vehicle', 'current_station', 'destination_station'
        ).order_by('-actual_start', '-scheduled_start')[:50]
        return Response(TripSerializer(trips, many=True).data)


class LiveVehiclesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.core.cache import cache
        return Response({
            "message": "Fallback API REST actif. Les positions sont en cache Redis."
        })


class DriverScheduleAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def get(self, request):
        if not Trip.objects.filter(driver_id=request.user.id).exists():
            line, _ = Line.objects.get_or_create(
                name='TGM',
                defaults={'color_code': '#0000FF'}
            )
            trajet, _ = Trajet.objects.get_or_create(
                line=line,
                name='Tunis -> Marsa',
                defaults={'path_coordinates': '36.8065,10.1815;36.8833,10.3293'}
            )
            vehicle, _ = Vehicle.objects.get_or_create(
                plate_number='123-TU-4567',
                defaults={'fleet_id': 'TGM-001', 'capacity': 300}
            )
            Trip.objects.create(
                trajet=trajet,
                vehicle=vehicle,
                driver_id=request.user.id,
                scheduled_start=timezone.now(),
                status='SCHEDULED',
            )

        trips = Trip.objects.filter(driver_id=request.user.id).select_related('trajet', 'vehicle').order_by('scheduled_start')
        return Response(TripSerializer(trips, many=True).data)


class DriverTripSetupAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def get(self, request):
        buses = Vehicle.objects.filter(is_active=True).filter(Q(driver_id=request.user.id) | Q(driver_id__isnull=True))
        trajets = Trajet.objects.filter(is_active=True).prefetch_related('trajet_stations__station')
        return Response({
            'buses': VehicleSerializer(buses, many=True).data,
            'trajets': TrajetWithStationsSerializer(trajets, many=True).data,
        })


class DriverStationTripStartAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def post(self, request):
        serializer = DriverTripStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        bus = get_object_or_404(Vehicle, id=data['bus_id'], is_active=True)
        if bus.driver_id and bus.driver_id != request.user.id:
            return Response({'detail': 'Ce bus est affecté à un autre conducteur.'}, status=400)

        trajet = get_object_or_404(Trajet, id=data['trajet_id'], is_active=True)
        trajet_stations = list(TrajetStation.objects.filter(trajet=trajet).select_related('station').order_by('order_number'))
        if len(trajet_stations) < 2:
            return Response({'detail': 'Le trajet doit avoir au moins 2 stations.'}, status=400)

        current_station = trajet_stations[0].station
        destination_station = trajet_stations[-1].station

        bus.driver_id = request.user.id
        bus.save(update_fields=['driver_id'])

        trip = Trip.objects.create(
            trajet=trajet,
            vehicle=bus,
            driver_id=request.user.id,
            current_station=current_station,
            destination_station=destination_station,
            scheduled_start=timezone.now(),
            actual_start=timezone.now(),
            status='IN_PROGRESS',
        )
        return Response(TripSerializer(trip).data, status=201)


class DriverStationTripUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def post(self, request, trip_id):
        trip = get_object_or_404(
            Trip.objects.select_related('trajet', 'vehicle', 'current_station', 'destination_station'),
            id=trip_id,
            driver_id=request.user.id,
        )
        if trip.status == 'COMPLETED':
            return Response({'detail': 'Impossible de mettre à jour un trajet terminé.'}, status=400)
        if trip.status != 'IN_PROGRESS':
            return Response({'detail': 'Le trajet doit être démarré avant la mise à jour.'}, status=400)
        trip = move_trip_to_next_station(trip)
        return Response(TripSerializer(trip).data)


class DriverStartTripAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def post(self, request, trip_id):
        trip = get_object_or_404(Trip.objects.select_related('trajet', 'vehicle'), id=trip_id, driver_id=request.user.id)
        if trip.status not in ['SCHEDULED', 'IN_PROGRESS']:
            return Response({'detail': 'Ce trajet ne peut pas être démarré.'}, status=400)

        if not trip.actual_start:
            trip.actual_start = timezone.now()
        trip.status = 'IN_PROGRESS'
        trip.save(update_fields=['actual_start', 'status'])
        return Response(TripSerializer(trip).data)


class DriverEndTripAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def post(self, request, trip_id):
        trip = get_object_or_404(Trip.objects.select_related('trajet', 'vehicle'), id=trip_id, driver_id=request.user.id)
        if trip.status != 'IN_PROGRESS':
            return Response({'detail': 'Seul un trajet en cours peut être terminé.'}, status=400)

        trip.actual_end = timezone.now()
        trip.status = 'COMPLETED'
        trip.save(update_fields=['actual_end', 'status'])
        return Response(TripSerializer(trip).data)


class DriverGPSUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def post(self, request, trip_id):
        trip = get_object_or_404(
            Trip.objects.select_related('trajet', 'vehicle', 'current_station', 'destination_station'),
            id=trip_id,
            driver_id=request.user.id,
        )
        if trip.status != 'IN_PROGRESS':
            return Response({'detail': 'GPS ignored: le trajet doit être actif.'}, status=400)

        serializer = GPSUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        trip.last_latitude = data['lat']
        trip.last_longitude = data['lng']
        trip.last_gps_update_time = timezone.now()
        trip.save(update_fields=['last_latitude', 'last_longitude', 'last_gps_update_time'])

        gps_log = GPSLog.objects.create(
            trip=trip,
            vehicle_id=trip.vehicle_id,
            location_lat=data['lat'],
            location_lng=data['lng'],
            speed_kmh=data.get('speed_kmh', 0),
            heading=data.get('heading', 0),
            recorded_at=timezone.now(),
        )

        next_ts = get_next_trajet_station(trip)
        if not next_ts:
            trip.status = 'COMPLETED'
            trip.actual_end = timezone.now()
            trip.save(update_fields=['status', 'actual_end'])
        elif next_ts.station.location_lat is not None and next_ts.station.location_lng is not None:
            distance_to_next = distance_meters(data['lat'], data['lng'], next_ts.station.location_lat, next_ts.station.location_lng)
            if distance_to_next <= 80:
                trip = move_trip_to_next_station(trip)

        return Response({
            'gps_log': GPSLogSerializer(gps_log).data,
            'trip': TripSerializer(trip).data,
        }, status=201)


class DriverIncidentAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def get(self, request):
        incidents = DriverIncident.objects.filter(driver_id=request.user.id).order_by('-created_at')[:50]
        return Response(DriverIncidentSerializer(incidents, many=True).data)

    def post(self, request):
        serializer = DriverIncidentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        trip = None
        if data.get('trip_id'):
            trip = get_object_or_404(Trip, id=data['trip_id'], driver_id=request.user.id)

        incident = DriverIncident.objects.create(
            trip=trip,
            driver_id=request.user.id,
            type=data['type'],
            description=data['description'],
            location_lat=data.get('location_lat'),
            location_lng=data.get('location_lng'),
        )
        return Response(DriverIncidentSerializer(incident).data, status=201)


from rest_framework import viewsets
from .serializers import StationSerializer

class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer
    permission_classes = [IsAuthenticated]


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all().order_by('plate_number')
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class LineViewSet(viewsets.ModelViewSet):
    queryset = Line.objects.all().order_by('name')
    serializer_class = LineSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class TrajetViewSet(viewsets.ModelViewSet):
    queryset = Trajet.objects.all().order_by('name')
    serializer_class = TrajetAdminSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class TrajetStationViewSet(viewsets.ModelViewSet):
    queryset = TrajetStation.objects.all().order_by('trajet_id', 'order_number')
    serializer_class = TrajetStationAdminSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class ImportedStationViewSet(viewsets.ModelViewSet):
    queryset = ImportedStation.objects.all().order_by('-created_at')
    serializer_class = ImportedStationSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class ImportedRouteViewSet(viewsets.ModelViewSet):
    queryset = ImportedRoute.objects.all().order_by('-created_at')
    serializer_class = ImportedRouteSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class ImportedRouteStationViewSet(viewsets.ModelViewSet):
    queryset = ImportedRouteStation.objects.all().order_by('imported_route', 'order_number')
    serializer_class = ImportedRouteStationSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class GTFSImportAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded = request.FILES.get('file')
        if not uploaded or not uploaded.name.endswith('.zip'):
            return Response({'detail': 'Le fichier doit être un ZIP GTFS.'}, status=400)

        try:
            with zipfile.ZipFile(uploaded) as zf:
                created = parse_and_import_gtfs(zf)
        except ValueError as e:
            return Response({'detail': str(e)}, status=400)
        except Exception as e:
            return Response({'detail': f'Erreur de lecture du ZIP: {str(e)}'}, status=400)

        return Response({'detail': 'Importation GTFS réussie.', 'created': created})


class GTFSSyncAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        import requests as http_requests
        url = (
            'https://catalogue-data.transport.tn/dataset/fe6c29b8-86c8-44cd-b36d-d41b70fab3f2/'
            'resource/841146b3-8dc9-4b23-88f2-880d64a50f34/download/'
            'fe6c29b8-86c8-44cd-b36d-d41b70fab3f2_41e5bb3e-3ef6-4d1e-ba29-e504601ab17b.zip'
        )
        try:
            resp = http_requests.get(url, timeout=120)
            resp.raise_for_status()
        except Exception as e:
            return Response({'detail': f'Erreur de téléchargement TRANSTU: {str(e)}'}, status=502)

        try:
            zf = zipfile.ZipFile(io.BytesIO(resp.content))
            created = parse_and_import_gtfs(zf)
        except ValueError as e:
            return Response({'detail': str(e)}, status=400)
        except Exception as e:
            return Response({'detail': f'Erreur d\'importation: {str(e)}'}, status=400)

        return Response({'detail': 'Synchronisation TRANSTU réussie.', 'created': created})


class DriverStartJourneyAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def post(self, request):
        serializer = StartJourneySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        trajet = get_object_or_404(Trajet, id=serializer.validated_data['trajet_id'])
        departure_station = get_object_or_404(Station, id=serializer.validated_data['departure_station_id'])
        arrival_station = get_object_or_404(Station, id=serializer.validated_data['arrival_station_id'])

        if departure_station.id == arrival_station.id:
            return Response({'detail': 'Le départ et l\'arrivée ne peuvent pas être identiques.'}, status=400)

        departure_order = get_station_order(trajet.id, departure_station.id)
        arrival_order = get_station_order(trajet.id, arrival_station.id)

        if departure_order is None:
            return Response({'detail': 'La station de départ n\'est pas sur cette route.'}, status=400)
        if arrival_order is None:
            return Response({'detail': 'La station d\'arrivée n\'est pas sur cette route.'}, status=400)
        if departure_order >= arrival_order:
            return Response({'detail': 'La station de départ doit être avant la station d\'arrivée.'}, status=400)

        if DriverSession.objects.filter(driver_id=request.user.id, status__in=['IN_PROGRESS', 'ARRIVED_AT_STATION']).exists():
            return Response({'detail': 'Vous avez déjà un trajet actif. Terminez-le avant d\'en commencer un nouveau.'}, status=400)

        session = DriverSession.objects.create(
            driver_id=request.user.id,
            trajet=trajet,
            departure_station=departure_station,
            arrival_station=arrival_station,
            current_station=departure_station,
            current_order=departure_order,
            status='IN_PROGRESS',
            started_at=timezone.now(),
        )
        return Response(DriverSessionSerializer(session).data, status=201)


class DriverUpdateStationAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def post(self, request):
        session = DriverSession.objects.filter(
            driver_id=request.user.id, status__in=['IN_PROGRESS', 'ARRIVED_AT_STATION']
        ).first()
        if not session:
            return Response({'detail': 'Aucun trajet actif trouvé.'}, status=400)

        serializer = UpdateStationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_station = get_object_or_404(Station, id=serializer.validated_data['station_id'])
        target_order = get_station_order(session.trajet_id, target_station.id)

        if target_order is None:
            return Response({'detail': 'Cette station n\'est pas sur cette route.'}, status=400)
        if target_order <= session.current_order:
            return Response({'detail': 'Vous ne pouvez que progresser vers l\'avant. Choisissez une station après la position actuelle.'}, status=400)

        session.current_station = target_station
        session.current_order = target_order
        session.updated_at = timezone.now()

        if target_order >= get_station_order(session.trajet_id, session.arrival_station_id):
            session.status = 'FINISHED'
            session.finished_at = timezone.now()
        else:
            session.status = 'ARRIVED_AT_STATION'

        session.save(update_fields=['current_station', 'current_order', 'updated_at', 'status', 'finished_at'])
        return Response(DriverSessionSerializer(session).data)


class DriverFinishJourneyAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def post(self, request):
        session = DriverSession.objects.filter(
            driver_id=request.user.id, status__in=['IN_PROGRESS', 'ARRIVED_AT_STATION']
        ).first()
        if not session:
            return Response({'detail': 'Aucun trajet actif trouvé.'}, status=400)

        session.status = 'FINISHED'
        session.finished_at = timezone.now()
        session.current_station = session.arrival_station
        session.current_order = get_station_order(session.trajet_id, session.arrival_station_id)
        session.save(update_fields=['status', 'finished_at', 'current_station', 'current_order'])
        return Response(DriverSessionSerializer(session).data)


class DriverCurrentJourneyAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def get(self, request):
        session = DriverSession.objects.filter(
            driver_id=request.user.id, status__in=['IN_PROGRESS', 'ARRIVED_AT_STATION']
        ).select_related('trajet', 'departure_station', 'arrival_station', 'current_station').first()

        if not session:
            return Response({'detail': 'Aucun trajet actif.', 'active': None})

        upcoming = TrajetStation.objects.filter(
            trajet=session.trajet, order_number__gte=session.current_order
        ).select_related('station').order_by('order_number')

        return Response({
            'active': DriverSessionSerializer(session).data,
            'upcoming_stations': TrajetStationSerializer(upcoming, many=True).data,
        })


class UserSearchBusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from_station_id = request.query_params.get('from_station_id')
        to_station_id = request.query_params.get('to_station_id')

        if not from_station_id or not to_station_id:
            return Response({'detail': 'Paramètres requis: from_station_id, to_station_id.'}, status=400)

        from_station = get_object_or_404(Station, id=from_station_id)
        to_station = get_object_or_404(Station, id=to_station_id)

        if from_station.id == to_station.id:
            return Response({'detail': 'La station de départ et d\'arrivée doivent être différentes.'}, status=400)

        sessions = DriverSession.objects.filter(
            status__in=['IN_PROGRESS', 'ARRIVED_AT_STATION']
        ).select_related('trajet', 'current_station', 'departure_station', 'arrival_station')

        results = []
        for session in sessions:
            current_order = session.current_order
            from_order = get_station_order(session.trajet_id, from_station.id)
            to_order = get_station_order(session.trajet_id, to_station.id)

            if from_order is None or to_order is None:
                continue
            if current_order >= from_order:
                continue
            if to_order <= from_order:
                continue

            user_stations_objects = get_trajet_stations_between(session.trajet_id, from_order, to_order)

            bus_to_user = get_trajet_stations_between(session.trajet_id, current_order, from_order)
            eta_minutes = calculate_eta(bus_to_user, 0)

            user_stations_data = []
            destination_stations_data = []
            for rs in user_stations_objects:
                station_eta = calculate_eta(bus_to_user, 0) + calculate_eta(
                    get_trajet_stations_between(session.trajet_id, from_order, rs.order_number), 0
                )
                entry = {
                    'id': str(rs.station_id),
                    'name': rs.station.name,
                    'order': rs.order_number,
                    'eta_minutes': station_eta,
                }
                if rs.order_number < to_order:
                    user_stations_data.append(entry)
                else:
                    destination_stations_data.append(entry)

            user_stations_data.append({
                'id': str(from_station.id),
                'name': from_station.name,
                'order': from_order,
                'eta_minutes': eta_minutes,
            })

            user_stations_data.sort(key=lambda x: x['order'])

            results.append(BusSearchResultSerializer({
                'driver_session_id': session.id,
                'driver_id': session.driver_id,
                'trajet_name': session.trajet.name,
                'bus_current_station': session.current_station,
                'bus_current_order': session.current_order,
                'user_stations': user_stations_data,
                'destination_stations': destination_stations_data,
                'status': session.status,
            }).data)

        return Response({'results': results})


class FetchStationsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        city = request.data.get('city')
        station_type = request.data.get('station_type')

        if not city or not station_type:
            return Response({'detail': 'Les champs "city" et "station_type" sont requis.'}, status=400)

        station_type = station_type.upper()
        valid_types = ['BUS', 'METRO', 'TRAIN']
        if station_type not in valid_types:
            return Response({'detail': f'station_type doit être l\'un des suivants: {", ".join(valid_types)}'}, status=400)

        try:
            result = fetch_and_store_stations(city, station_type)
            return Response(result)
        except ValueError as e:
            return Response({'detail': str(e)}, status=400)
        except Exception as e:
            return Response({'detail': f'Erreur lors de la récupération des stations: {str(e)}'}, status=502)


class PromoteStationsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        serializer = PromoteStationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        imported_ids = serializer.validated_data['imported_station_ids']
        imported_stations = ImportedStation.objects.filter(id__in=imported_ids)

        promoted = 0
        for imp in imported_stations:
            station, created = Station.objects.update_or_create(
                name=imp.name,
                defaults={
                    'location_lat': imp.latitude,
                    'location_lng': imp.longitude,
                    'is_verified': True,
                }
            )
            imp.approved_station = station
            imp.is_approved = True
            imp.save(update_fields=['approved_station', 'is_approved'])
            promoted += 1

        return Response({'detail': f'{promoted} stations promues vers la production.'})


class PromoteRoutesAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        serializer = PromoteRouteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        imported_ids = serializer.validated_data['imported_route_ids']
        imported_routes = ImportedRoute.objects.filter(id__in=imported_ids).prefetch_related('imported_stations__imported_station')

        gtfs_line, _ = Line.objects.get_or_create(
            name='Réseau GTFS',
            defaults={'color_code': '#00A8FF', 'is_active': True},
        )

        promoted = 0
        for imp in imported_routes:
            trajet, created = Trajet.objects.update_or_create(
                name=imp.name,
                defaults={
                    'line': gtfs_line,
                    'is_active': True,
                }
            )

            route_stations = imp.imported_stations.all().order_by('order_number')
            for rs in route_stations:
                imp_station = rs.imported_station
                if not imp_station.approved_station:
                    station, _ = Station.objects.update_or_create(
                        name=imp_station.name,
                        defaults={
                            'location_lat': imp_station.latitude,
                            'location_lng': imp_station.longitude,
                            'is_verified': True,
                        }
                    )
                    imp_station.approved_station = station
                    imp_station.is_approved = True
                    imp_station.save(update_fields=['approved_station', 'is_approved'])
                else:
                    station = imp_station.approved_station

                TrajetStation.objects.update_or_create(
                    trajet=trajet,
                    station=station,
                    defaults={
                        'order_number': rs.order_number,
                        'time_to_next_station': rs.time_to_next_station,
                    }
                )

            ordered = list(TrajetStation.objects.filter(trajet=trajet).order_by('order_number'))
            if ordered:
                trajet.start_station = ordered[0].station
                trajet.end_station = ordered[-1].station
                trajet.save(update_fields=['start_station', 'end_station'])

            imp.approved_trajet = trajet
            imp.is_approved = True
            imp.save(update_fields=['approved_trajet', 'is_approved'])
            promoted += 1

        return Response({'detail': f'{promoted} routes importées vers la production.'})


class AdminImportSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        return Response({
            'imported_stations': ImportedStation.objects.count(),
            'imported_routes': ImportedRoute.objects.count(),
            'imported_route_stations': ImportedRouteStation.objects.count(),
            'pending_stations': ImportedStation.objects.filter(is_approved=False).count(),
            'pending_routes': ImportedRoute.objects.filter(is_approved=False).count(),
            'stations': Station.objects.count(),
            'trajets': Trajet.objects.count(),
        })
