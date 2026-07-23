import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User, Profile
from doctors.models import Specialty
from doctors.models.general import TimeRange, Monday
from bookings.models import Booking
from datetime import date, time, timedelta

@pytest.mark.django_db
class TestVoiceAIEndpoints:
    @pytest.fixture(autouse=True)
    def setup_method(self, db):
        self.client = APIClient()

        # Create doctor
        self.doctor = User.objects.create_user(
            username="dr_priya",
            email="priya@doccure.com",
            password="password123",
            first_name="Priya",
            last_name="Sharma",
            role=User.RoleChoices.DOCTOR
        )
        self.doctor_profile = self.doctor.profile
        self.doctor_profile.phone = "9999999999"
        self.doctor_profile.specialization = "Cardiology"
        self.doctor_profile.save()

        # Setup specialty (department)
        self.specialty = Specialty.objects.create(name="Cardiology", description="Heart Specialist")
        self.specialty.doctors.add(self.doctor)

        # Setup schedule for Monday
        self.time_range = TimeRange.objects.create(
            start=time(14, 0),
            end=time(14, 30),
            slots_per_hour=4  # 15 min slots
        )
        self.monday_schedule = Monday.objects.create(user=self.doctor)
        self.monday_schedule.time_range.add(self.time_range)

        # Create patient
        self.patient = User.objects.create_user(
            username="pat_caller",
            email="caller@doccure.com",
            password="password123",
            first_name="Test",
            last_name="Caller",
            role=User.RoleChoices.PATIENT
        )
        self.patient_profile = self.patient.profile
        self.patient_profile.phone = "9876543210"
        self.patient_profile.save()

        # Create admin (to authenticate API calls since we need a token)
        self.admin = User.objects.create_superuser(
            username="admin_api",
            email="admin@doccure.com",
            password="password123"
        )

    def get_auth_client(self):
        response = self.client.post(reverse('api:login'), {
            "email": "admin@doccure.com",
            "password": "password123"
        })
        assert response.status_code == status.HTTP_200_OK
        token = response.data['data']['token']
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        return client

    def test_login(self):
        response = self.client.post(reverse('api:login'), {
            "email": "admin@doccure.com",
            "password": "password123"
        })
        assert response.status_code == status.HTTP_200_OK
        assert 'token' in response.data['data']

    def test_customer_lookup_found(self):
        client = self.get_auth_client()
        response = client.get(reverse('api:customer_lookup') + '?phone=9876543210')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['name'] == "Test Caller"

    def test_customer_lookup_not_found(self):
        client = self.get_auth_client()
        response = client.get(reverse('api:customer_lookup') + '?phone=1111111111')
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['success'] is False

    def test_register_patient_new(self):
        client = self.get_auth_client()
        response = client.post(reverse('api:register_patient'), {
            "name": "New Caller",
            "phone": "5555555555",
            "gender": "male",
            "age": 25
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['already_registered'] is False
        assert User.objects.filter(profile__phone="5555555555").exists()

    def test_register_patient_existing(self):
        client = self.get_auth_client()
        response = client.post(reverse('api:register_patient'), {
            "name": "Test Caller",
            "phone": "9876543210",
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['already_registered'] is True

    def test_departments_list(self):
        client = self.get_auth_client()
        response = client.get(reverse('api:departments'))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert len(response.data['data']['departments']) == 1
        assert response.data['data']['departments'][0]['department'] == "Cardiology"

    def test_doctors_list(self):
        client = self.get_auth_client()
        response = client.get(reverse('api:doctors') + '?department=Cardiology')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert len(response.data['data']['doctors']) == 1

    def test_doctor_schedule_fuzzy(self):
        client = self.get_auth_client()
        response = client.get(reverse('api:doctor_schedule') + '?name=priya&days=7')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['data']['doctor_id'] == self.doctor.id

    def test_book_appointment_success(self):
        client = self.get_auth_client()
        today = date.today()
        days_ahead = 0 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_monday = today + timedelta(days=days_ahead)

        response = client.post(reverse('api:book_appointment'), {
            "doctor_id": self.doctor.id,
            "patient_id": self.patient.id,
            "date": next_monday.strftime("%Y-%m-%d"),
            "time": "14:15",
            "notes": "Regular checkup"
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True

    def test_my_appointments(self):
        client = self.get_auth_client()
        # Create a booking first
        booking = Booking.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            appointment_date=date.today() + timedelta(days=1),
            appointment_time=time(14, 0),
            status='pending'
        )
        response = client.get(reverse('api:my_appointments') + '?phone=9876543210')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']['appointments']) == 1

    def test_reschedule_appointment(self):
        client = self.get_auth_client()
        booking = Booking.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            appointment_date=date.today() + timedelta(days=1),
            appointment_time=time(14, 0),
            status='pending'
        )
        today = date.today()
        days_ahead = 0 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_monday = today + timedelta(days=days_ahead)

        response = client.post(reverse('api:reschedule_appointment'), {
            "appointment_id": booking.id,
            "date": next_monday.strftime("%Y-%m-%d"),
            "time": "14:15"
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True

    def test_cancel_appointment(self):
        client = self.get_auth_client()
        booking = Booking.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            appointment_date=date.today() + timedelta(days=1),
            appointment_time=time(14, 0),
            status='pending'
        )
        response = client.post(reverse('api:cancel_appointment'), {
            "appointment_id": booking.id,
            "reason": "Changed my mind"
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        booking.refresh_from_db()
        assert booking.status == 'cancelled'
