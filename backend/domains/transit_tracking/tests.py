from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from domains.auth_identity.models import User
from domains.transit_tracking.models import (
    DriverSession, Line, Trajet, TrajetStation, Station, Vehicle,
)


class DriverJourneyBaseTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.driver = User.objects.create_user(
            phone_number='+21650111111',
            password='Test123!',
            role='DRIVER',
            first_name='Test',
            last_name='Driver',
            email='driver@test.tn',
        )
        cls.passenger = User.objects.create_user(
            phone_number='+21650222222',
            password='Test123!',
            role='PASSENGER',
            email='passenger@test.tn',
        )

        cls.station_a = Station.objects.create(
            name='Station A', location_lat=36.80, location_lng=10.18
        )
        cls.station_b = Station.objects.create(
            name='Station B', location_lat=36.82, location_lng=10.20
        )
        cls.station_c = Station.objects.create(
            name='Station C', location_lat=36.84, location_lng=10.22
        )
        cls.station_d = Station.objects.create(
            name='Station D', location_lat=36.86, location_lng=10.24
        )
        cls.station_e = Station.objects.create(
            name='Station E', location_lat=36.88, location_lng=10.26
        )

        cls.line = Line.objects.create(name='Test Line', color_code='#FF0000')

        cls.trajet = Trajet.objects.create(
            line=cls.line, name='Test Trajet',
            start_station=cls.station_a, end_station=cls.station_e,
        )

        cls.rs_a = TrajetStation.objects.create(
            trajet=cls.trajet, station=cls.station_a, order_number=1, time_to_next_station=5
        )
        cls.rs_b = TrajetStation.objects.create(
            trajet=cls.trajet, station=cls.station_b, order_number=2, time_to_next_station=4
        )
        cls.rs_c = TrajetStation.objects.create(
            trajet=cls.trajet, station=cls.station_c, order_number=3, time_to_next_station=6
        )
        cls.rs_d = TrajetStation.objects.create(
            trajet=cls.trajet, station=cls.station_d, order_number=4, time_to_next_station=3
        )
        cls.rs_e = TrajetStation.objects.create(
            trajet=cls.trajet, station=cls.station_e, order_number=5, time_to_next_station=0
        )

        cls.bus = Vehicle.objects.create(
            plate_number='100-TU-100',
            fleet_id='BUS-100',
            capacity=200,
            is_active=True,
        )
        cls.bus2 = Vehicle.objects.create(
            plate_number='200-TU-200',
            fleet_id='BUS-200',
            capacity=150,
            is_active=True,
        )

    def setUp(self):
        self.client = APIClient()


class DriverStartJourneyTest(DriverJourneyBaseTest):
    """Tests for POST /driver/start/"""

    def _auth(self, user=None):
        user = user or self.driver
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_start_valid_journey(self):
        self._auth()
        resp = self.client.post(reverse('api_driver_start_journey'), {
            'trajet_id': self.trajet.id,
            'departure_station_id': self.station_a.id,
            'arrival_station_id': self.station_d.id,
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        data = resp.data
        self.assertEqual(data['status'], 'IN_PROGRESS')
        self.assertEqual(data['current_station']['id'], str(self.station_a.id))
        self.assertEqual(data['current_order'], 1)

    def test_departure_arrival_same(self):
        self._auth()
        resp = self.client.post(reverse('api_driver_start_journey'), {
            'trajet_id': self.trajet.id,
            'departure_station_id': self.station_a.id,
            'arrival_station_id': self.station_a.id,
        }, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('identiques', resp.data['detail'])

    def test_departure_after_arrival(self):
        self._auth()
        resp = self.client.post(reverse('api_driver_start_journey'), {
            'trajet_id': self.trajet.id,
            'departure_station_id': self.station_d.id,
            'arrival_station_id': self.station_a.id,
        }, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('avant', resp.data['detail'])

    def test_station_not_on_trajet(self):
        self._auth()
        other = Station.objects.create(name='Other', location_lat=0, location_lng=0)
        resp = self.client.post(reverse('api_driver_start_journey'), {
            'trajet_id': self.trajet.id,
            'departure_station_id': other.id,
            'arrival_station_id': self.station_d.id,
        }, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_duplicate_active_session_blocked(self):
        self._auth()
        self.client.post(reverse('api_driver_start_journey'), {
            'trajet_id': self.trajet.id,
            'departure_station_id': self.station_a.id,
            'arrival_station_id': self.station_d.id,
        }, format='json')
        resp = self.client.post(reverse('api_driver_start_journey'), {
            'trajet_id': self.trajet.id,
            'departure_station_id': self.station_b.id,
            'arrival_station_id': self.station_e.id,
        }, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('actif', resp.data['detail'])

    def test_unauthenticated_blocked(self):
        resp = self.client.post(reverse('api_driver_start_journey'), {
            'trajet_id': self.trajet.id,
            'departure_station_id': self.station_a.id,
            'arrival_station_id': self.station_d.id,
        }, format='json')
        self.assertEqual(resp.status_code, 401)


class DriverUpdateStationTest(DriverJourneyBaseTest):
    """Tests for POST /driver/update-station/"""

    def setUp(self):
        super().setUp()
        refresh = RefreshToken.for_user(self.driver)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        self.client.post(reverse('api_driver_start_journey'), {
            'trajet_id': self.trajet.id,
            'departure_station_id': self.station_a.id,
            'arrival_station_id': self.station_d.id,
        }, format='json')

    def test_update_to_next_station(self):
        resp = self.client.post(reverse('api_driver_update_station'), {
            'station_id': self.station_b.id,
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['current_station']['id'], str(self.station_b.id))
        self.assertEqual(resp.data['current_order'], 2)
        self.assertEqual(resp.data['status'], 'ARRIVED_AT_STATION')

    def test_update_to_final_station_finishes(self):
        self.client.post(reverse('api_driver_update_station'), {
            'station_id': self.station_b.id,
        }, format='json')
        self.client.post(reverse('api_driver_update_station'), {
            'station_id': self.station_c.id,
        }, format='json')
        resp = self.client.post(reverse('api_driver_update_station'), {
            'station_id': self.station_d.id,
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['status'], 'FINISHED')
        self.assertIsNotNone(resp.data['finished_at'])

    def test_update_to_previous_station_blocked(self):
        self.client.post(reverse('api_driver_update_station'), {
            'station_id': self.station_b.id,
        }, format='json')
        resp = self.client.post(reverse('api_driver_update_station'), {
            'station_id': self.station_a.id,
        }, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('progresser', resp.data['detail'])

    def test_update_to_wrong_trajet_station_blocked(self):
        other = Station.objects.create(name='Other', location_lat=0, location_lng=0)
        resp = self.client.post(reverse('api_driver_update_station'), {
            'station_id': other.id,
        }, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('pas sur cette route', resp.data['detail'])

    def test_no_active_session_blocked(self):
        DriverSession.objects.filter(driver_id=self.driver.id).update(status='FINISHED')
        resp = self.client.post(reverse('api_driver_update_station'), {
            'station_id': self.station_b.id,
        }, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('actif', resp.data['detail'])


class DriverFinishJourneyTest(DriverJourneyBaseTest):
    """Tests for POST /driver/finish/"""

    def setUp(self):
        super().setUp()
        refresh = RefreshToken.for_user(self.driver)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        self.client.post(reverse('api_driver_start_journey'), {
            'trajet_id': self.trajet.id,
            'departure_station_id': self.station_a.id,
            'arrival_station_id': self.station_d.id,
        }, format='json')

    def test_finish_active_session(self):
        resp = self.client.post(reverse('api_driver_finish_journey'), {}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['status'], 'FINISHED')
        self.assertIsNotNone(resp.data['finished_at'])
        self.assertEqual(resp.data['current_station']['id'], str(self.station_d.id))

    def test_finish_no_active_session(self):
        DriverSession.objects.filter(driver_id=self.driver.id).update(status='FINISHED')
        resp = self.client.post(reverse('api_driver_finish_journey'), {}, format='json')
        self.assertEqual(resp.status_code, 400)


class DriverCurrentJourneyTest(DriverJourneyBaseTest):
    """Tests for GET /driver/current/"""

    def setUp(self):
        super().setUp()
        refresh = RefreshToken.for_user(self.driver)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_no_active_session(self):
        resp = self.client.get(reverse('api_driver_current_journey'))
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.data['active'])

    def test_active_session_with_upcoming(self):
        self.client.post(reverse('api_driver_start_journey'), {
            'trajet_id': self.trajet.id,
            'departure_station_id': self.station_a.id,
            'arrival_station_id': self.station_d.id,
        }, format='json')
        resp = self.client.get(reverse('api_driver_current_journey'))
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.data['active'])
        self.assertEqual(len(resp.data['upcoming_stations']), 5)


class UserSearchBusTest(DriverJourneyBaseTest):
    """Tests for GET /user/search-bus/"""

    def setUp(self):
        super().setUp()
        refresh = RefreshToken.for_user(self.driver)
        d1_client = APIClient()
        d1_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        d1_client.post(reverse('api_driver_start_journey'), {
            'trajet_id': self.trajet.id,
            'departure_station_id': self.station_a.id,
            'arrival_station_id': self.station_d.id,
        }, format='json')

        p_refresh = RefreshToken.for_user(self.passenger)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {p_refresh.access_token}')

    def test_search_valid_returns_bus(self):
        resp = self.client.get(reverse('api_user_search_bus'), {
            'from_station_id': self.station_b.id,
            'to_station_id': self.station_d.id,
        })
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(len(resp.data['results']), 1)

    def test_search_from_after_bus_current(self):
        resp = self.client.get(reverse('api_user_search_bus'), {
            'from_station_id': self.station_b.id,
            'to_station_id': self.station_d.id,
        })
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(len(resp.data['results']), 1)

    def test_search_from_before_bus_current_invalid(self):
        resp = self.client.get(reverse('api_user_search_bus'), {
            'from_station_id': self.station_a.id,
            'to_station_id': self.station_d.id,
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['results']), 0)

    def test_search_to_before_from_invalid(self):
        resp = self.client.get(reverse('api_user_search_bus'), {
            'from_station_id': self.station_d.id,
            'to_station_id': self.station_b.id,
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['results']), 0)

    def test_search_same_station_invalid(self):
        resp = self.client.get(reverse('api_user_search_bus'), {
            'from_station_id': self.station_b.id,
            'to_station_id': self.station_b.id,
        })
        self.assertEqual(resp.status_code, 400)

    def test_eta_calculation(self):
        resp = self.client.get(reverse('api_user_search_bus'), {
            'from_station_id': self.station_b.id,
            'to_station_id': self.station_d.id,
        })
        self.assertEqual(resp.status_code, 200, msg=resp.data)
        result = resp.data['results'][0]
        user_stations = result['user_stations']
        bus_station = result['bus_current_station']['name']
        self.assertEqual(bus_station, 'Station A')
        self.assertTrue(len(user_stations) >= 1)

    def test_unauthenticated_blocked(self):
        self.client.credentials()
        resp = self.client.get(reverse('api_user_search_bus'), {
            'from_station_id': self.station_b.id,
            'to_station_id': self.station_d.id,
        })
        self.assertEqual(resp.status_code, 401)
