from datetime import date, datetime
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.db.models import Q
from accounts.models import User, Profile
from bookings.models import Booking
from api.utils import get_next_available_slot

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            username = None

        if username:
            user = authenticate(username=username, password=password)
        else:
            user = None

        if not user:
            raise serializers.ValidationError("Invalid email or password.")

        attrs['user'] = user
        return attrs


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data['password']

        # Generate a unique username from email
        prefix = email.split('@')[0]
        clean_prefix = "".join(c for c in prefix if c.isalnum() or c in '_-')[:20]
        if not clean_prefix:
            clean_prefix = "user"

        username = clean_prefix
        counter = 1
        while User.objects.filter(username=username).exists():
            suffix = str(counter)
            username = f"{clean_prefix[:30-len(suffix)]}{suffix}"
            counter += 1

        user = User.objects.create(
            username=username,
            email=email,
            role=User.RoleChoices.PATIENT,
            is_active=True
        )
        user.set_password(password)
        user.save()
        return user



class PatientSerializer(serializers.ModelSerializer):
    patient_id = serializers.IntegerField(source='id', read_only=True)
    name = serializers.SerializerMethodField()
    phone = serializers.CharField(source='profile.phone', required=False, allow_null=True)
    gender = serializers.CharField(source='profile.gender', required=False, default='other')
    age = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['patient_id', 'name', 'phone', 'gender', 'age']

    def get_name(self, obj):
        return obj.get_full_name() or obj.username

    def get_age(self, obj):
        if obj.profile.dob:
            today = date.today()
            dob = obj.profile.dob
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return None


class BookingResponseSerializer(serializers.ModelSerializer):
    appointment_id = serializers.IntegerField(source='id', read_only=True)
    token = serializers.SerializerMethodField()
    doctor = serializers.SerializerMethodField()
    patient = serializers.SerializerMethodField()
    date = serializers.DateField(source='appointment_date')
    time = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = ['appointment_id', 'token', 'doctor', 'patient', 'date', 'time', 'status']

    def get_token(self, obj):
        return f"APT-{obj.id:03d}"

    def get_doctor(self, obj):
        return f"Dr. {obj.doctor.get_full_name()}"

    def get_patient(self, obj):
        return obj.patient.get_full_name()

    def get_time(self, obj):
        return obj.appointment_time.strftime("%H:%M")


class DoctorSerializer(serializers.ModelSerializer):
    doctor_id = serializers.IntegerField(source='id')
    name = serializers.SerializerMethodField()
    specialization = serializers.SerializerMethodField()
    next_available = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['doctor_id', 'name', 'specialization', 'next_available']

    def get_name(self, obj):
        return f"Dr. {obj.get_full_name()}"

    def get_specialization(self, obj):
        return obj.profile.specialization or "General Physician"

    def get_next_available(self, obj):
        return get_next_available_slot(obj)


class DepartmentSerializer(serializers.Serializer):
    department = serializers.CharField(source='name')
    doctor_count = serializers.SerializerMethodField()
    doctors = serializers.SerializerMethodField()

    def get_doctor_count(self, obj):
        return self.get_doctors_queryset(obj).count()

    def get_doctors(self, obj):
        doctors = self.get_doctors_queryset(obj)
        return DoctorSerializer(doctors, many=True).data

    def get_doctors_queryset(self, obj):
        name = obj.name.lower()
        if 'neuro' in name:
            query = Q(profile__specialization__icontains='neuro')
        elif 'ortho' in name:
            query = Q(profile__specialization__icontains='ortho')
        elif 'cardio' in name:
            query = Q(profile__specialization__icontains='cardio')
        elif 'dent' in name:
            query = Q(profile__specialization__icontains='dent')
        elif 'uro' in name:
            query = Q(profile__specialization__icontains='uro') & ~Q(profile__specialization__icontains='neuro')
        else:
            query = Q(profile__specialization__icontains=name)

        return User.objects.filter(
            role=User.RoleChoices.DOCTOR,
            is_active=True
        ).filter(query)


class AppointmentSerializer(serializers.ModelSerializer):
    appointment_id = serializers.IntegerField(source='id')
    doctor = serializers.SerializerMethodField()
    date = serializers.DateField(source='appointment_date')
    time = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = ['appointment_id', 'doctor', 'date', 'time', 'status']

    def get_doctor(self, obj):
        return f"Dr. {obj.doctor.get_full_name()}"

    def get_time(self, obj):
        return obj.appointment_time.strftime("%H:%M")
