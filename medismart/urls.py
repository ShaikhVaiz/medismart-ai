from django.contrib import admin
from django.urls import path, include
from tracker import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/signup/", views.signup, name="signup"),
    path("accounts/forgot-password/", views.forgot_password, name="forgot_password"),
    path("accounts/verify-otp/", views.verify_otp, name="verify_otp"),
    path("app/", include("tracker.urls")),
]
