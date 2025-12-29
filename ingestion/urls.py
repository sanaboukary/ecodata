from django.urls import path
from .views import health, start_ingestion

urlpatterns = [
    path("health/", health, name="ingestion-health"),
    path("start/", start_ingestion, name="ingestion-start"),
]
