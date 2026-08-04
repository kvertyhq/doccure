import django
import os
import sys

# Add root folder to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Initialize Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "doccure.settings")
django.setup()

from accounts.models import User
import urllib.request
import urllib.parse
import json

def main():
    base_url = "http://127.0.0.1:8000"
    
    # Query patient1 and doctor1 info dynamically from DB
    patient = User.objects.filter(username="patient1").first()
    if not patient:
        print("patient1 not found in DB.")
        sys.exit(1)
        
    doc = User.objects.filter(username="doctor1").first()
    if not doc:
        print("doctor1 not found in DB.")
        sys.exit(1)
        
    patient_email = patient.email
    patient_phone = patient.profile.phone
    doc_name = doc.first_name

    print(f"Patient email: {patient_email}")
    print(f"Patient phone: {patient_phone}")
    print(f"Doctor search name: {doc_name}")

    # 1. Login to get Auth Token
    login_url = f"{base_url}/api/v1/auth/login"
    login_data = json.dumps({
        "email": patient_email,
        "password": "password123"
    }).encode("utf-8")
    
    req = urllib.request.Request(
        login_url,
        data=login_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode())
            print("Login response:")
            print(json.dumps(res_data, indent=2))
            token = res_data["data"]["token"]
    except urllib.error.HTTPError as e:
        print(f"Failed login (HTTPError): {e.code} {e.reason}")
        print(e.read().decode())
        sys.exit(1)
    except Exception as e:
        print(f"Failed login: {e}")
        sys.exit(1)

    # Note the change to Bearer token format
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    # 2. Customer Lookup using existing phone number
    lookup_url = f"{base_url}/api/v1/customer?phone={urllib.parse.quote(patient_phone)}"
    req = urllib.request.Request(
        lookup_url,
        headers=headers,
        method="GET"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode())
            print("\nCustomer Lookup response:")
            print(json.dumps(res_data, indent=2))
    except urllib.error.HTTPError as e:
        print(f"Failed customer lookup (HTTPError): {e.code} {e.reason}")
        print(e.read().decode())
        sys.exit(1)
    except Exception as e:
        print(f"Failed customer lookup: {e}")
        sys.exit(1)

    # 3. Get doctor schedule
    schedule_url = f"{base_url}/api/v1/doctor-schedule?name={urllib.parse.quote(doc_name)}&days=10"
    req = urllib.request.Request(
        schedule_url,
        headers=headers,
        method="GET"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode())
            print("\nDoctor Schedule response:")
            print(json.dumps({
                "success": res_data["success"],
                "doctor_id": res_data["data"]["doctor_id"],
                "name": res_data["data"]["name"],
                "available_slots_keys": list(res_data["data"]["available_slots"].keys())[:3]
            }, indent=2))
            
            # Find a valid slot that has available slots
            available_slots = res_data["data"]["available_slots"]
            target_date = None
            target_time = None
            for d_str, slots in available_slots.items():
                if slots:
                    target_date = d_str
                    target_time = slots[0]
                    break
            
            if not target_date or not target_time:
                print("No slots available in the next 10 days.")
                sys.exit(1)
                
            print(f"Found available slot on {target_date} at {target_time}")
            doctor_id = res_data["data"]["doctor_id"]
    except Exception as e:
        print(f"Failed doctor schedule lookup: {e}")
        sys.exit(1)

    # 4. Book an appointment
    book_url = f"{base_url}/api/v1/book-appointment"
    book_data = json.dumps({
        "doctor_id": doctor_id,
        "phone": patient_phone,
        "date": target_date,
        "time": target_time,
        "notes": "Testing appointment booking via API."
    }).encode("utf-8")
    
    req = urllib.request.Request(
        book_url,
        data=book_data,
        headers=headers,
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode())
            print("\nBook Appointment response:")
            print(json.dumps(res_data, indent=2))
    except urllib.error.HTTPError as e:
        print(f"Failed booking (HTTPError): {e.code} {e.reason}")
        print(e.read().decode())
        sys.exit(1)
    except Exception as e:
        print(f"Failed booking: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
