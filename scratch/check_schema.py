from django.db import connection
import django
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'doccure.settings')
django.setup()

cursor = connection.cursor()
cursor.execute("SELECT table_schema, table_name FROM information_schema.tables WHERE table_name = 'doccure_core_speciality'")
print("Schema info:", cursor.fetchall())

cursor.execute("SHOW search_path")
print("Search path:", cursor.fetchall())

cursor.execute("SELECT current_user")
print("Current user:", cursor.fetchall())
