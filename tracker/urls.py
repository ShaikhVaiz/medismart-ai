from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("medicines/", views.medicine_list, name="medicine_list"),
    path("medicines/add/", views.medicine_create, name="medicine_create"),
    path("medicines/scan-prescription/", views.scan_prescription, name="scan_prescription"),
    path("medicines/<int:pk>/edit/", views.medicine_edit, name="medicine_edit"),
    path("medicines/<int:pk>/delete/", views.medicine_delete, name="medicine_delete"),
    path("medicines/<int:pk>/dose/<str:status>/", views.record_dose, name="record_dose"),
    path("family/", views.family_list, name="family_list"),
    path("family/add/", views.family_create, name="family_create"),
    path("refills/", views.refill_list, name="refill_list"),
    path("medicines/<int:pk>/refill/", views.refill_create, name="refill_create"),
]
