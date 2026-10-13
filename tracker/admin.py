from django.contrib import admin
from .models import FamilyProfile, Medicine, MedicineSchedule, DoseLog, Pharmacy, RefillRequest, PasswordResetOTP

class ScheduleInline(admin.TabularInline):
    model = MedicineSchedule
    extra = 0

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "profile", "stock_quantity", "expiry_date")
    search_fields = ("name", "owner__username")
    inlines = [ScheduleInline]

admin.site.register(FamilyProfile)
admin.site.register(DoseLog)
admin.site.register(Pharmacy)
admin.site.register(RefillRequest)

@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    list_display = ("user", "otp", "created_at", "is_used")
    search_fields = ("user__username", "user__email", "otp")
