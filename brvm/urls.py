from django.urls import path
from .views_recommendations import recommendations_brvm
from .views import run_brvm_pipeline
from .views_refresh import refresh_pipeline_brvm
from .classement_views import classement_objectif

urlpatterns = [
    path("brvm/recommendations/", recommendations_brvm, name="brvm_recommendations"),
    path("brvm/recommendations/refresh/", refresh_pipeline_brvm, name="refresh_pipeline_brvm"),
    path("run-pipeline/", run_brvm_pipeline, name="run_pipeline"),
    path("classement/", classement_objectif, name="classement_objectif"),
]
