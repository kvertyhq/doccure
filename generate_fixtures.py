import json
import random

def generate_fixtures():
    # Set seed for reproducibility so names and emails do not change on future runs
    random.seed(42)
    # Default password for all users: password123
    fixtures = []

    # Real Bangladeshi names
    bd_male_first_names = [
        "Abdul", "Mohammad", "Ahmed", "Kamal", "Jamal",
        "Rashid", "Mahmud", "Sajid", "Rafiq", "Hasan",
        "Mehedi", "Sharif", "Nasir", "Fahim", "Rahim"
    ]
    bd_male_last_names = [
        "Rahman", "Islam", "Hossain", "Ahmed", "Uddin",
        "Khan", "Chowdhury", "Talukder", "Siddique", "Ali",
        "Sheikh", "Miah", "Sarkar", "Molla", "Majumder"
    ]
    bd_female_first_names = [
        "Fatima", "Aisha", "Nusrat", "Taslima", "Sabina",
        "Nasreen", "Rahima", "Salma", "Amina", "Jasmine",
        "Sultana", "Roksana", "Sadia", "Nahida", "Farzana"
    ]
    bd_female_last_names = [
        "Begum", "Khatun", "Akter", "Rahman", "Islam",
        "Hossain", "Ahmed", "Khan", "Chowdhury", "Sultana",
        "Siddiqua", "Jahan", "Parvin", "Nahar", "Akhter"
    ]

    # Real Indian names
    in_male_first_names = [
        "Amit", "Rahul", "Arjun", "Sanjay", "Vijay",
        "Rajesh", "Vikram", "Anil", "Sunil", "Rohan",
        "Aditya", "Dev", "Karan", "Manish", "Suresh"
    ]
    in_male_last_names = [
        "Sharma", "Verma", "Gupta", "Kumar", "Singh",
        "Patel", "Mehta", "Joshi", "Rao", "Nair",
        "Mishra", "Trivedi", "Banerjee", "Chatterjee", "Reddy"
    ]
    in_female_first_names = [
        "Priya", "Anjali", "Neha", "Pooja", "Deepika",
        "Kiran", "Aditi", "Shweta", "Ritu", "Sunita",
        "Divya", "Kavita", "Meera", "Asha", "Sangeeta"
    ]
    in_female_last_names = [
        "Sharma", "Verma", "Gupta", "Sen", "Singh",
        "Patel", "Iyer", "Reddy", "Nair", "Joshi",
        "Deshmukh", "Chawla", "Bose", "Das", "Pillai"
    ]

    spec_mapping = [
        ("Urologist", "Urology", "urology"),
        ("Neurologist", "Neurology", "neurology"),
        ("Orthopedic Surgeon", "Orthopedic", "orthopedic"),
        ("Cardiologist", "Cardiologist", "cardiologist"),
        ("Dentist", "Dentist", "dentist"),
        ("Pediatrician", "Pediatrician", "pediatrician"),
        ("Gynecologist", "Gynecologist", "gynecologist"),
        ("Dermatologist", "Dermatologist", "dermatologist")
    ]

    bd_cities = [
        "Dhaka", "Chittagong", "Sylhet", "Rajshahi", "Khulna",
        "Barisal", "Rangpur", "Mymensingh", "Cox's Bazar",
        "Comilla", "Narayanganj", "Gazipur"
    ]
    bd_divisions = [
        "Dhaka", "Chittagong", "Sylhet", "Rajshahi", "Khulna",
        "Barisal", "Rangpur", "Mymensingh"
    ]
    bd_areas = [
        "Gulshan", "Banani", "Dhanmondi", "Uttara", "Mirpur",
        "Mohammadpur", "Badda", "Khilgaon"
    ]

    in_cities = [
        "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai",
        "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Lucknow",
        "Chandigarh", "Indore"
    ]
    in_states = [
        "Maharashtra", "Delhi", "Karnataka", "Telangana", "Tamil Nadu",
        "West Bengal", "Uttar Pradesh", "Gujarat", "Rajasthan", "Madhya Pradesh"
    ]
    in_areas = [
        "Andheri", "Bandra", "Connaught Place", "Indiranagar", "Jubilee Hills",
        "T. Nagar", "Salt Lake", "Koregaon Park", "C.G. Road", "Malviya Nagar"
    ]

    # Add core.speciality fixtures
    for idx, (spec_name, dept_name, slug) in enumerate(spec_mapping, start=1):
        fixtures.append({
            "model": "core.speciality",
            "pk": idx,
            "fields": {
                "name": dept_name,
                "slug": slug,
                "description": f"{dept_name} department",
                "is_active": True
            }
        })

    # Add TimeRange fixtures for doctor schedules
    fixtures.append({
        "model": "doctors.timerange",
        "pk": 1,
        "fields": {
            "start": "09:00:00",
            "end": "12:00:00",
            "is_active": True,
            "slots_per_hour": 4
        }
    })
    fixtures.append({
        "model": "doctors.timerange",
        "pk": 2,
        "fields": {
            "start": "14:00:00",
            "end": "17:00:00",
            "is_active": True,
            "slots_per_hour": 4
        }
    })

    # Generate 24 doctors (3 for each of the 8 departments)
    # Let's make doctors with even indices Indian, and odd indices Bangladeshi
    for i in range(1, 25):
        # Determine specialization based on index
        spec_idx = (i - 1) // 3
        specialization = spec_mapping[spec_idx][0]

        # Determine user & profile ID
        if i <= 15:
            doc_user_id = i
        else:
            doc_user_id = 35 + (i - 16)

        gender = random.choice(["male", "female"])
        is_indian = (i % 2 == 0)

        if is_indian:
            country = "India"
            city = random.choice(in_cities)
            state = random.choice(in_states)
            postal_code = f"{random.randint(110000, 700000)}"
            address = f"Flat {random.randint(1, 100)}, {random.choice(in_areas)}, {city}"
            phone = f"+919876{i:06d}"
            med_college = random.choice(['All India Institute of Medical Sciences', 'King George\'s Medical University', 'Christian Medical College', 'Armed Forces Medical College'])
            if gender == "male":
                first_name = random.choice(in_male_first_names)
                last_name = random.choice(in_male_last_names)
            else:
                first_name = random.choice(in_female_first_names)
                last_name = random.choice(in_female_last_names)
        else:
            country = "Bangladesh"
            city = random.choice(bd_cities)
            state = random.choice(bd_divisions)
            postal_code = f"{random.randint(1000, 9999)}"
            address = f"House {random.randint(1, 99)}, Road {random.randint(1, 15)}, Block {random.choice(['A', 'B', 'C', 'D'])}, {random.choice(bd_areas)}"
            phone = f"+880175{i:07d}"
            med_college = random.choice(['Dhaka Medical College', 'Chittagong Medical College', 'Sylhet Medical College', 'Rajshahi Medical College'])
            if gender == "male":
                first_name = random.choice(bd_male_first_names)
                last_name = random.choice(bd_male_last_names)
            else:
                first_name = random.choice(bd_female_first_names)
                last_name = random.choice(bd_female_last_names)

        doctor_username = f"doctor{i}"
        doctor = {
            "model": "accounts.user",
            "pk": doc_user_id,
            "fields": {
                "password": "pbkdf2_sha256$720000$IHF1VtxSDbZcIAr0YsiGLJ$+qez0fhZFOIX5Be+7n4thX19eN2xCGS4b5o75lIXYJ0=",  # "password123"
                "username": doctor_username,
                "email": f"{first_name.lower()}.{last_name.lower()}@example.com",
                "first_name": first_name,
                "last_name": last_name,
                "role": "doctor",
                "is_active": True,
                "date_joined": "2023-01-01T00:00:00Z",
            },
        }
        fixtures.append(doctor)

        # Doctor Profile
        doctor_profile = {
            "model": "accounts.profile",
            "pk": doc_user_id,
            "fields": {
                "user": doc_user_id,
                "phone": phone,
                "dob": f"{random.randint(1960, 1990)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                "about": f"MBBS from {med_college}. {random.randint(5, 20)} years of experience in {specialization}.",
                "specialization": specialization,
                "gender": gender,
                "address": address,
                "city": city,
                "state": state,
                "postal_code": postal_code,
                "country": country,
                "price_per_consultation": random.randint(500, 2000),
                "is_available": True,
            },
        }
        fixtures.append(doctor_profile)

        # Generate weekly schedules for this doctor for all days of the week
        for day in ["saturday", "sunday", "monday", "tuesday", "wednesday", "thursday", "friday"]:
            fixtures.append({
                "model": f"doctors.{day}",
                "pk": i,  # unique pk for each weekday schedule record
                "fields": {
                    "user": doc_user_id,
                    "time_range": [1, 2]
                }
            })

    # Generate 15 patients
    # Let's make patients with even indices Indian, and odd indices Bangladeshi
    for i in range(1, 16):
        gender = random.choice(["male", "female"])
        is_indian = (i % 2 == 0)

        if is_indian:
            country = "India"
            city = random.choice(in_cities)
            state = random.choice(in_states)
            postal_code = f"{random.randint(110000, 700000)}"
            address = f"Flat {random.randint(1, 50)}, {random.choice(in_areas)}, {city}"
            phone = f"+919856{i:06d}"
            if gender == "male":
                first_name = random.choice(in_male_first_names)
                last_name = random.choice(in_male_last_names)
            else:
                first_name = random.choice(in_female_first_names)
                last_name = random.choice(in_female_last_names)
        else:
            country = "Bangladesh"
            city = random.choice(bd_cities)
            state = random.choice(bd_divisions)
            postal_code = f"{random.randint(1000, 9999)}"
            address = f"Flat {random.randint(1, 20)}A, House {random.randint(1, 99)}, Road {random.randint(1, 15)}, {random.choice(bd_areas)}"
            phone = f"+880185{i:07d}"
            if gender == "male":
                first_name = random.choice(bd_male_first_names)
                last_name = random.choice(bd_male_last_names)
            else:
                first_name = random.choice(bd_female_first_names)
                last_name = random.choice(bd_female_last_names)

        patient_user_id = 15 + i
        patient_username = f"patient{i}"
        patient = {
            "model": "accounts.user",
            "pk": patient_user_id,
            "fields": {
                "password": "pbkdf2_sha256$720000$IHF1VtxSDbZcIAr0YsiGLJ$+qez0fhZFOIX5Be+7n4thX19eN2xCGS4b5o75lIXYJ0=",  # "password123"
                "username": patient_username,
                "email": f"{first_name.lower()}.{last_name.lower()}@example.com",
                "first_name": first_name,
                "last_name": last_name,
                "role": "patient",
                "is_active": True,
                "date_joined": "2023-01-01T00:00:00Z",
            },
        }
        fixtures.append(patient)

        # Patient Profile
        blood_groups = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]
        patient_profile = {
            "model": "accounts.profile",
            "pk": patient_user_id,
            "fields": {
                "user": patient_user_id,
                "phone": phone,
                "dob": f"{random.randint(1970, 2000)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                "gender": gender,
                "address": address,
                "city": city,
                "state": state,
                "postal_code": postal_code,
                "country": country,
                "blood_group": random.choice(blood_groups),
                "allergies": random.choice(["None", "Dust Allergy", "Food Allergy", "Drug Allergy"]),
                "medical_conditions": random.choice(["None", "High Blood Pressure", "Diabetes", "Asthma"]),
            },
        }
        fixtures.append(patient_profile)

    # Write fixtures to file
    with open("fixtures/initial_data.json", "w") as f:
        json.dump(fixtures, f, indent=2)

if __name__ == "__main__":
    generate_fixtures()
