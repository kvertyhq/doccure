import json
from datetime import datetime, date, timedelta
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from accounts.models import User, Profile
from core.models import Speciality
from bookings.models import Booking
from api.serializers import (
    LoginSerializer,
    SignupSerializer,
    PatientSerializer,
    BookingResponseSerializer,
    DoctorSerializer,
    DepartmentSerializer,
    AppointmentSerializer
)
from api.utils import (
    get_available_slots_for_date,
    get_next_available_slot,
    cache_api_response,
    invalidate_api_cache
)

class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            "success": True,
            "data": {
                "token": token.key
            }
        })


class SignupAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = SignupSerializer

    def post(self, request):
        print("DEBUG: Request Data:", request.data)
        print("DEBUG: Content Type:", request.content_type)
        serializer = SignupSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            "success": True,
            "message": "User registered successfully.",
            "data": {
                "token": token.key,
                "email": user.email,
                "username": user.username
            }
        }, status=status.HTTP_201_CREATED)


class CustomerLookupAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PatientSerializer

    @cache_api_response()
    def get(self, request):
        phone = request.query_params.get('phone')
        if not phone:
            return Response({
                "success": False,
                "message": "Phone number is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        clean_phone = ''.join(filter(str.isdigit, phone))
        if not clean_phone:
            return Response({
                "success": False,
                "message": "number was not found register him as a new patient"
            }, status=status.HTTP_200_OK)

        if len(clean_phone) > 10:
            clean_phone = clean_phone[-10:]

        try:
            profile = Profile.objects.filter(
                user__role=User.RoleChoices.PATIENT,
                phone__endswith=clean_phone
            ).select_related('user').first()

            if not profile:
                return Response({
                    "success": False,
                    "message": "number was not found register him as a new patient"
                }, status=status.HTTP_200_OK)

            user = profile.user
            serializer = PatientSerializer(user)
            return Response({
                "success": True,
                "data": serializer.data
            })
        except Exception as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PatientRegisterAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PatientSerializer

    def post(self, request):
        name = request.data.get('name')
        phone = request.data.get('phone')
        gender = request.data.get('gender', 'unknown')
        age = request.data.get('age')

        if not name or not phone:
            return Response({
                "success": False,
                "message": "Name and phone are required."
            }, status=status.HTTP_400_BAD_REQUEST)

        clean_phone = ''.join(filter(str.isdigit, phone))
        if not clean_phone:
            return Response({
                "success": False,
                "message": "Invalid phone number."
            }, status=status.HTTP_400_BAD_REQUEST)

        if len(clean_phone) > 10:
            clean_phone = clean_phone[-10:]

        existing_profile = Profile.objects.filter(
            user__role=User.RoleChoices.PATIENT,
            phone__endswith=clean_phone
        ).select_related('user').first()

        if existing_profile:
            user = existing_profile.user
            return Response({
                "success": True,
                "data": {
                    "patient_id": user.id,
                    "phone": existing_profile.phone,
                    "name": user.get_full_name(),
                    "already_registered": True
                }
            })

        name_parts = name.strip().split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        db_gender = 'other'
        if gender.lower() in ['male', 'female']:
            db_gender = gender.lower()

        dob = None
        if age is not None:
            try:
                age_val = int(age)
                dob = date.today() - timedelta(days=age_val * 365.25)
            except ValueError:
                pass

        username = f"pat_{clean_phone}"
        user = User.objects.create(
            username=username,
            first_name=first_name,
            last_name=last_name,
            role=User.RoleChoices.PATIENT,
            is_active=True
        )
        user.set_password(User.objects.make_random_password())
        user.save()

        profile = user.profile
        profile.phone = phone
        profile.gender = db_gender
        if dob:
            profile.dob = dob
        profile.save()

        return Response({
            "success": True,
            "data": {
                "patient_id": user.id,
                "phone": phone,
                "name": name,
                "already_registered": False
            }
        })


class BookAppointmentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookingResponseSerializer

    def post(self, request):
        doctor_id = request.data.get('doctor_id')
        patient_id = request.data.get('patient_id')
        phone = request.data.get('phone')
        date_str = request.data.get('date')
        time_str = request.data.get('time')
        notes = request.data.get('notes', '')

        if not doctor_id or not date_str or not time_str:
            return Response({
                "success": False,
                "message": "doctor_id, date, and time are required."
            }, status=status.HTTP_400_BAD_REQUEST)

        doctor = get_object_or_404(User, id=doctor_id, role=User.RoleChoices.DOCTOR)

        patient = None
        if patient_id:
            patient = get_object_or_404(User, id=patient_id, role=User.RoleChoices.PATIENT)
        elif phone:
            clean_phone = ''.join(filter(str.isdigit, phone))
            if len(clean_phone) > 10:
                clean_phone = clean_phone[-10:]
            profile = Profile.objects.filter(
                user__role=User.RoleChoices.PATIENT,
                phone__endswith=clean_phone
            ).select_related('user').first()
            if profile:
                patient = profile.user

        if not patient:
            return Response({
                "success": False,
                "message": "Patient not found. Please register the patient first."
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            appointment_time = datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            return Response({
                "success": False,
                "message": "Invalid date or time format. Use YYYY-MM-DD and HH:MM."
            }, status=status.HTTP_400_BAD_REQUEST)

        combined_dt = datetime.combine(appointment_date, appointment_time)
        if combined_dt < datetime.now():
            return Response({
                "success": False,
                "message": "Appointment slot must be in the future."
            }, status=status.HTTP_400_BAD_REQUEST)

        day_name = appointment_date.strftime("%A").lower()
        day_schedule = getattr(doctor, day_name, None)
        if not day_schedule:
            return Response({
                "success": False,
                "message": f"Doctor does not work on {appointment_date.strftime('%A')}."
            }, status=status.HTTP_400_BAD_REQUEST)

        time_ranges = day_schedule.time_range.all()
        slot_found = False
        for tr in time_ranges:
            if tr.start <= appointment_time < tr.end:
                start_mins = tr.start.hour * 60 + tr.start.minute
                req_mins = appointment_time.hour * 60 + appointment_time.minute
                duration = tr.get_slot_duration()
                if (req_mins - start_mins) % duration == 0:
                    slot_found = True
                    break

        if not slot_found:
            return Response({
                "success": False,
                "message": "Doctor is not available at the requested time slot."
            }, status=status.HTTP_400_BAD_REQUEST)

        is_booked = doctor.appointments.filter(
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            status__in=['pending', 'confirmed', 'completed']
        ).exists()

        if is_booked:
            return Response({
                "success": False,
                "message": "This slot is already booked."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            booking = Booking.objects.create(
                doctor=doctor,
                patient=patient,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status='pending'
            )
            invalidate_api_cache()
            serializer = BookingResponseSerializer(booking)
            return Response({
                "success": True,
                "data": serializer.data
            })
        except IntegrityError:
            return Response({
                "success": False,
                "message": "This slot is already booked."
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DepartmentListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DepartmentSerializer

    @cache_api_response()
    def get(self, request):
        try:
            specialties = Speciality.objects.filter(is_active=True)
            serializer = DepartmentSerializer(specialties, many=True)

            summary_parts = []
            raw_departments = []

            for dept in serializer.data:
                dept_name = dept.get("department", "")
                doctors = dept.get("doctors", [])

                if doctors:
                    doc_strs = [
                        f"{doc['name']} (ID: {doc['doctor_id']})"
                        for doc in doctors
                        if doc.get("name") and doc.get("doctor_id")
                    ]
                    if doc_strs:
                        summary_parts.append(f"{dept_name}: {', '.join(doc_strs)}")

                    raw_doctors = [
                        {
                            "doctor_id": doc["doctor_id"],
                            "name": doc["name"]
                        }
                        for doc in doctors
                        if doc.get("doctor_id") and doc.get("name")
                    ]
                    if raw_doctors:
                        raw_departments.append({
                            "department": dept_name,
                            "doctors": raw_doctors
                        })

            summary = " | ".join(summary_parts)
            raw_json_string = json.dumps(raw_departments, separators=(',', ':'))

            return Response({
                "success": True,
                "summary": summary,
                "raw_json_string": raw_json_string
            })
        except Exception as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DoctorListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DoctorSerializer

    @cache_api_response()
    def get(self, request):
        dept_name = request.query_params.get('department')
        doctors = User.objects.filter(
            role=User.RoleChoices.DOCTOR,
            is_active=True
        ).select_related(
            'profile',
            'saturday',
            'sunday',
            'monday',
            'tuesday',
            'wednesday',
            'thursday',
            'friday'
        ).prefetch_related(
            'appointments',
            'saturday__time_range',
            'sunday__time_range',
            'monday__time_range',
            'tuesday__time_range',
            'wednesday__time_range',
            'thursday__time_range',
            'friday__time_range'
        )

        if dept_name:
            doctors = doctors.filter(specialties__name__iexact=dept_name)


        serializer = DoctorSerializer(doctors, many=True)
        return Response({
            "success": True,
            "data": {
                "doctors": serializer.data
            }
        })


class DoctorScheduleAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DoctorSerializer # fallback for documentation

    @cache_api_response()
    def get(self, request, *args, **kwargs):
        doctor_id = kwargs.get('doctor_id') or request.query_params.get('doctor_id') or request.query_params.get('id')
        name = request.query_params.get('name')
        date_param = request.query_params.get('date')

        if not doctor_id and not name:
            return Response({
                "success": False,
                "message": "doctor_id or name is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        base_qs = User.objects.filter(
            role=User.RoleChoices.DOCTOR,
            is_active=True
        ).select_related(
            'saturday',
            'sunday',
            'monday',
            'tuesday',
            'wednesday',
            'thursday',
            'friday'
        ).prefetch_related(
            'saturday__time_range',
            'sunday__time_range',
            'monday__time_range',
            'tuesday__time_range',
            'wednesday__time_range',
            'thursday__time_range',
            'friday__time_range'
        )

        doctor = None
        if doctor_id:
            try:
                doctor = base_qs.filter(id=int(doctor_id)).first()
            except (ValueError, TypeError):
                return Response({
                    "success": False,
                    "message": "Invalid doctor_id."
                }, status=status.HTTP_400_BAD_REQUEST)

        if not doctor and name:
            # Safely remove "Dr." or "Dr" prefix from the start of the name only
            clean_name = name.strip()
            if clean_name.lower().startswith("dr."):
                clean_name = clean_name[3:].strip()
            elif clean_name.lower().startswith("dr "):
                clean_name = clean_name[3:].strip()
            elif clean_name.lower() == "dr":
                clean_name = ""

            # Normalize spaces
            clean_name = " ".join(clean_name.split())

            from django.db.models.functions import Concat
            from django.db.models import Value

            doctor = base_qs.annotate(
                full_name=Concat('first_name', Value(' '), 'last_name')
            ).filter(
                Q(first_name__icontains=clean_name) | 
                Q(last_name__icontains=clean_name) |
                Q(full_name__icontains=clean_name)
            ).first()

        if not doctor:
            return Response({
                "success": False,
                "message": "Doctor not found."
            }, status=status.HTTP_404_NOT_FOUND)

        target_dates = []
        if date_param:
            try:
                parsed_date = datetime.strptime(date_param.strip(), "%Y-%m-%d").date()
                target_dates = [parsed_date]
            except ValueError:
                return Response({
                    "success": False,
                    "message": "Invalid date format. Expected YYYY-MM-DD."
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            days_str = request.query_params.get('days', '7')
            try:
                days = min(max(int(days_str), 1), 30)
            except ValueError:
                days = 7
            today = date.today()
            target_dates = [today + timedelta(days=i) for i in range(days)]

        min_date = min(target_dates)
        max_date = max(target_dates)
        booked_slots = set(
            doctor.appointments.filter(
                appointment_date__range=(min_date, max_date),
                status__in=['pending', 'confirmed', 'completed']
            ).values_list('appointment_date', 'appointment_time')
        )

        schedule = {}
        for target_date in target_dates:
            slots = get_available_slots_for_date(doctor, target_date, booked_slots=booked_slots)
            schedule[target_date.strftime("%Y-%m-%d")] = slots

        active_dates = [d for d, slots in schedule.items() if slots]
        available_dates = ", ".join(active_dates)
        slots_summary = " | ".join([f"{d}: {', '.join(schedule[d])}" for d in active_dates])

        response_payload = {
            "success": True,
            "doctor_id": doctor.id,
            "doctor_name": f"Dr. {doctor.get_full_name()}",
            "available_dates": available_dates,
            "slots_summary": slots_summary,
            "data": {
                "doctor_id": doctor.id,
                "name": f"Dr. {doctor.get_full_name()}",
                "available_slots": schedule
            }
        }

        if date_param:
            date_key = target_dates[0].strftime("%Y-%m-%d")
            response_payload["date_slots"] = ", ".join(schedule.get(date_key, []))

        return Response(response_payload)


class MyAppointmentsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AppointmentSerializer

    @cache_api_response()
    def get(self, request):
        phone = request.query_params.get('phone')
        include_past_str = request.query_params.get('include_past', 'false')
        include_past = include_past_str.lower() == 'true'

        if not phone:
            return Response({
                "success": False,
                "message": "Phone or patient_id query parameter is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        bookings = Booking.objects.select_related('doctor', 'doctor__profile')

        clean_phone = ''.join(filter(str.isdigit, phone))
        if phone.isdigit() and len(phone) < 6:
            bookings = bookings.filter(patient_id=int(phone))
        else:
            if len(clean_phone) > 10:
                clean_phone = clean_phone[-10:]
            bookings = bookings.filter(patient__profile__phone__endswith=clean_phone)

        if not include_past:
            bookings = bookings.filter(appointment_date__gte=date.today())

        serializer = AppointmentSerializer(bookings, many=True)
        return Response({
            "success": True,
            "data": {
                "appointments": serializer.data
            }
        })


class RescheduleAppointmentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookingResponseSerializer

    def post(self, request):
        appointment_id = request.data.get('appointment_id')
        date_str = request.data.get('date')
        time_str = request.data.get('time')

        if not appointment_id or not date_str or not time_str:
            return Response({
                "success": False,
                "message": "appointment_id, date, and time are required."
            }, status=status.HTTP_400_BAD_REQUEST)

        booking = get_object_or_404(Booking, id=appointment_id)

        try:
            appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            appointment_time = datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            return Response({
                "success": False,
                "message": "Invalid date or time format. Use YYYY-MM-DD and HH:MM."
            }, status=status.HTTP_400_BAD_REQUEST)

        doctor = booking.doctor
        day_name = appointment_date.strftime("%A").lower()
        day_schedule = getattr(doctor, day_name, None)
        if not day_schedule:
            return Response({
                "success": False,
                "message": f"Doctor does not work on {appointment_date.strftime('%A')}."
            }, status=status.HTTP_400_BAD_REQUEST)

        time_ranges = day_schedule.time_range.all()
        slot_found = False
        for tr in time_ranges:
            if tr.start <= appointment_time < tr.end:
                start_mins = tr.start.hour * 60 + tr.start.minute
                req_mins = appointment_time.hour * 60 + appointment_time.minute
                duration = tr.get_slot_duration()
                if (req_mins - start_mins) % duration == 0:
                    slot_found = True
                    break

        if not slot_found:
            return Response({
                "success": False,
                "message": "Doctor is not available at the requested time slot."
            }, status=status.HTTP_400_BAD_REQUEST)

        is_booked = doctor.appointments.filter(
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            status__in=['pending', 'confirmed', 'completed']
        ).exclude(id=booking.id).exists()

        if is_booked:
            return Response({
                "success": False,
                "message": "This slot is already booked."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            booking.appointment_date = appointment_date
            booking.appointment_time = appointment_time
            booking.save()
            invalidate_api_cache()
            serializer = BookingResponseSerializer(booking)
            return Response({
                "success": True,
                "data": serializer.data
            })
        except Exception as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CancelAppointmentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookingResponseSerializer # fallback for documentation

    def post(self, request):
        appointment_id = request.data.get('appointment_id')
        reason = request.data.get('reason', '')

        if not appointment_id:
            return Response({
                "success": False,
                "message": "appointment_id is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        booking = get_object_or_404(Booking, id=appointment_id)
        booking.status = 'cancelled'
        booking.save()
        invalidate_api_cache()

        return Response({
            "success": True,
            "message": "Appointment cancelled successfully."
        })