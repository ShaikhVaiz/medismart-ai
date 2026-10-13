from datetime import date, timedelta
import secrets
from django.conf import settings
from django.db import models
from django.utils import timezone


class FamilyProfile(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="family_profiles")
    name = models.CharField(max_length=100)
    relationship = models.CharField(max_length=60, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.owner.username})"


class Medicine(models.Model):
    UNIT_CHOICES = [
        ("tablet", "Tablets"), ("capsule", "Capsules"), ("ml", "mL"),
        ("dose", "Doses"), ("bottle", "Bottles"), ("pack", "Packs"),
    ]
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="medicines")
    profile = models.ForeignKey(FamilyProfile, on_delete=models.CASCADE, null=True, blank=True, related_name="medicines")
    name = models.CharField(max_length=120)
    strength = models.CharField(max_length=80, blank=True, help_text="Example: 500 mg (as written on the prescription)")
    instructions = models.CharField(max_length=240, blank=True, help_text="Enter instructions exactly as prescribed")
    unit = models.CharField(max_length=12, choices=UNIT_CHOICES, default="tablet")
    stock_quantity = models.PositiveIntegerField(default=0)
    daily_usage = models.DecimalField(max_digits=7, decimal_places=2, default=1, help_text="Total units used per day, according to the prescription")
    refill_notice_days = models.PositiveSmallIntegerField(default=5)
    expiry_date = models.DateField(null=True, blank=True)
    pharmacy_link = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def days_remaining(self):
        usage = float(self.daily_usage)
        if usage <= 0:
            return None
        return int(self.stock_quantity / usage)

    @property
    def needs_refill(self):
        days = self.days_remaining
        return self.stock_quantity <= 0 or (days is not None and days <= self.refill_notice_days)

    @property
    def is_expired(self):
        return bool(self.expiry_date and self.expiry_date < date.today())


class MedicineSchedule(models.Model):
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name="schedules")
    time = models.TimeField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["time"]
        unique_together = ("medicine", "time")

    def __str__(self):
        return f"{self.medicine.name} at {self.time.strftime('%H:%M')}"


class DoseLog(models.Model):
    STATUS_CHOICES = [("taken", "Taken"), ("skipped", "Skipped")]
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="dose_logs")
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name="dose_logs")
    schedule = models.ForeignKey(MedicineSchedule, on_delete=models.SET_NULL, null=True, blank=True)
    scheduled_for = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-recorded_at"]


class Pharmacy(models.Model):
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)
    address = models.CharField(max_length=240, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class RefillRequest(models.Model):
    STATUS_CHOICES = [
        ("requested", "Requested"), ("confirmed", "Confirmed"),
        ("processing", "Processing"), ("ready", "Ready for pickup"),
        ("completed", "Completed"), ("cancelled", "Cancelled"),
    ]
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="refill_requests")
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name="refill_requests")
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.SET_NULL, null=True, blank=True)
    quantity_requested = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="requested")
    notes = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class PasswordResetOTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="password_otps")
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"OTP for {self.user.username} ({self.otp})"

    def is_valid(self):
        return (not self.is_used) and (timezone.now() - self.created_at <= timedelta(minutes=10))

    @classmethod
    def generate_otp_for_user(cls, user):
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        code = f"{secrets.randbelow(900000) + 100000:06d}"
        return cls.objects.create(user=user, otp=code)
