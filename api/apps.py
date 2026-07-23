from django.apps import AppConfig


import os

class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"
    path = os.path.dirname(os.path.abspath(__file__))
