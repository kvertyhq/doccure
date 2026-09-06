from django.urls import path
from api.views import (
    LoginAPIView,
    SignupAPIView,
    CustomerLookupAPIView,
    PatientRegisterAPIView,
    BookAppointmentAPIView,
    DepartmentListAPIView,
    DoctorListAPIView,
    DoctorScheduleAPIView,
    MyAppointmentsAPIView,
    RescheduleAppointmentAPIView,
    CancelAppointmentAPIView
)

app_name = "api"

urlpatterns = [
    path('auth/login', LoginAPIView.as_view(), name='login'),
    path('auth/signup', SignupAPIView.as_view(), name='signup'),

    path('customer', CustomerLookupAPIView.as_view(), name='customer_lookup'),
    path('register-patient', PatientRegisterAPIView.as_view(), name='register_patient'),
    path('book-appointment', BookAppointmentAPIView.as_view(), name='book_appointment'),
    path('departments', DepartmentListAPIView.as_view(), name='departments'),
    path('doctors', DoctorListAPIView.as_view(), name='doctors'),
    path('doctor-schedule', DoctorScheduleAPIView.as_view(), name='doctor_schedule'),
    path('doctors/<int:doctor_id>/slots', DoctorScheduleAPIView.as_view(), name='doctor_slots'),
    path('my-appointments', MyAppointmentsAPIView.as_view(), name='my_appointments'),
    path('reschedule-appointment', RescheduleAppointmentAPIView.as_view(), name='reschedule_appointment'),
    path('cancel-appointment', CancelAppointmentAPIView.as_view(), name='cancel_appointment'),
]
