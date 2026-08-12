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


import hashlib
import json
from functools import wraps
from django.core.cache import cache
from rest_framework.response import Response

def get_api_cache_version():
    try:
        return cache.get("api_cache_version", 1)
    except Exception:
        return 1

def invalidate_api_cache():
    try:
        cache.incr("api_cache_version")
    except ValueError:
        try:
            cache.set("api_cache_version", 2)
        except Exception:
            pass
    except Exception:
        pass

def cache_api_response(timeout=900, key_prefix="api_cache"):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(self, request, *args, **kwargs):
            if request.method != 'GET':
                return view_func(self, request, *args, **kwargs)
            
            try:
                query_params = sorted(request.query_params.items())
                params_str = json.dumps(query_params)
                params_hash = hashlib.md5(params_str.encode('utf-8')).hexdigest()
                version = get_api_cache_version()
                cache_key = f"{key_prefix}:{version}:{request.path}:{params_hash}"
                
                cached_data = cache.get(cache_key)
                if cached_data is not None:
                    return Response(cached_data)
            except Exception:
                cache_key = None
            
            response = view_func(self, request, *args, **kwargs)
            
            if cache_key is not None and response.status_code == 200:
                try:
                    cache.set(cache_key, response.data, timeout)
                except Exception:
                    pass
            return response
        return _wrapped_view
    return decorator
