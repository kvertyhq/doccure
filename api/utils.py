from datetime import datetime, date, time, timedelta
from bookings.models import Booking

def get_available_slots_for_date(doctor, target_date):
    day_name = target_date.strftime("%A").lower()
    day_schedule = getattr(doctor, day_name, None)

    if not day_schedule:
        return []

    time_slots = []
    # Fetch all time ranges for this day
    time_ranges = day_schedule.time_range.all()
    for tr in time_ranges:
        current_dt = datetime.combine(target_date, tr.start)
        end_dt = datetime.combine(target_date, tr.end)
        duration = tr.get_slot_duration()

        while current_dt < end_dt:
            slot_time = current_dt.time()
            
            # If target_date is today, slot must be in the future
            if target_date == date.today() and combined_in_past(target_date, slot_time):
                current_dt += timedelta(minutes=duration)
                continue

            # Check if booked
            is_booked = doctor.appointments.filter(
                appointment_date=target_date,
                appointment_time=slot_time,
                status__in=['pending', 'confirmed', 'completed']
            ).exists()

            if not is_booked:
                time_slots.append(slot_time.strftime("%H:%M"))
            current_dt += timedelta(minutes=duration)
            
    return sorted(list(set(time_slots)))

def combined_in_past(target_date, target_time):
    return datetime.combine(target_date, target_time) < datetime.now()

def get_next_available_slot(doctor):
    today = date.today()
    # Check next 30 days
    for i in range(30):
        target_date = today + timedelta(days=i)
        slots = get_available_slots_for_date(doctor, target_date)
        if slots:
            return f"{target_date.strftime('%Y-%m-%d')} {slots[0]}"
    return None
