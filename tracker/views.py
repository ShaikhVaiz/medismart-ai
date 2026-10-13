from datetime import date
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib.auth.models import User
from django.http import JsonResponse
from .forms import SignUpForm, MedicineForm, FamilyProfileForm, RefillRequestForm
from .models import Medicine, MedicineSchedule, DoseLog, FamilyProfile, Pharmacy, RefillRequest, PasswordResetOTP
from .emails import send_password_reset_otp_email
from .ai_scanner import scan_prescription_with_ai


def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "tracker/home.html")


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created. Welcome to MediSmart!")
            return redirect("dashboard")
    else:
        form = SignUpForm()
    return render(request, "registration/signup.html", {"form": form})


@login_required
def dashboard(request):
    today = timezone.localdate()
    medicines = Medicine.objects.filter(owner=request.user).select_related("profile")
    schedules = MedicineSchedule.objects.filter(medicine__owner=request.user, active=True).select_related("medicine").order_by("time")
    logs = DoseLog.objects.filter(owner=request.user, scheduled_for=today)
    logged_pairs = set(logs.values_list("medicine_id", "schedule_id", "status"))
    schedule_items = []
    for schedule in schedules:
        statuses = list(logs.filter(medicine=schedule.medicine, schedule=schedule).values_list("status", flat=True))
        schedule_items.append({
            "schedule": schedule,
            "time_text": schedule.time.strftime("%H:%M"),
            "already_recorded": bool(statuses),
            "status_text": statuses[-1] if statuses else "",
        })
    context = {
        "medicines": medicines,
        "schedules": schedule_items,
        "refill_count": sum(1 for m in medicines if m.needs_refill),
        "today": today,
        "recent_logs": logs[:8],
    }
    return render(request, "tracker/dashboard.html", context)


@login_required
def medicine_list(request):
    medicines = Medicine.objects.filter(owner=request.user).select_related("profile")
    return render(request, "tracker/medicine_list.html", {"medicines": medicines})


@login_required
def medicine_create(request):
    if request.method == "POST":
        form = MedicineForm(request.POST, user=request.user)
        if form.is_valid():
            medicine = form.save(commit=False)
            medicine.owner = request.user
            if medicine.profile and medicine.profile.owner_id != request.user.id:
                messages.error(request, "Invalid family profile.")
                return redirect("medicine_create")
            medicine.save()
            for time_text in form.cleaned_data["schedule_times"]:
                hour, minute = map(int, time_text.split(":"))
                MedicineSchedule.objects.get_or_create(medicine=medicine, time=f"{hour:02d}:{minute:02d}")
            messages.success(request, "Medicine saved.")
            return redirect("medicine_list")
    else:
        form = MedicineForm(user=request.user)
    return render(request, "tracker/medicine_form.html", {"form": form, "heading": "Add medicine"})


@login_required
def medicine_edit(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk, owner=request.user)
    if request.method == "POST":
        form = MedicineForm(request.POST, instance=medicine, user=request.user)
        if form.is_valid():
            item = form.save(commit=False)
            if item.profile and item.profile.owner_id != request.user.id:
                messages.error(request, "Invalid family profile.")
                return redirect("medicine_edit", pk=pk)
            item.save()
            # Editing schedule times replaces the schedule for this medicine.
            MedicineSchedule.objects.filter(medicine=medicine).delete()
            for time_text in form.cleaned_data["schedule_times"]:
                hour, minute = map(int, time_text.split(":"))
                MedicineSchedule.objects.create(medicine=medicine, time=f"{hour:02d}:{minute:02d}")
            messages.success(request, "Medicine updated.")
            return redirect("medicine_list")
    else:
        form = MedicineForm(instance=medicine, user=request.user)
        form.fields["schedule_times"].initial = ", ".join(s.time.strftime("%H:%M") for s in medicine.schedules.all())
    return render(request, "tracker/medicine_form.html", {"form": form, "heading": "Edit medicine"})


@login_required
def medicine_delete(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk, owner=request.user)
    if request.method == "POST":
        medicine.delete()
        messages.success(request, "Medicine deleted.")
        return redirect("medicine_list")
    return render(request, "tracker/confirm_delete.html", {"object": medicine})


@login_required
def record_dose(request, pk, status):
    if status not in {"taken", "skipped"}:
        messages.error(request, "Unknown dose status.")
        return redirect("dashboard")
    medicine = get_object_or_404(Medicine, pk=pk, owner=request.user)
    schedule_id = request.POST.get("schedule_id")
    schedule = None
    if schedule_id:
        schedule = get_object_or_404(MedicineSchedule, pk=schedule_id, medicine=medicine)
    if request.method == "POST":
        DoseLog.objects.create(owner=request.user, medicine=medicine, schedule=schedule,
                               scheduled_for=timezone.localdate(), status=status)
        if status == "taken" and medicine.stock_quantity > 0:
            medicine.stock_quantity -= 1
            medicine.save(update_fields=["stock_quantity"])
        messages.success(request, f"{medicine.name}: recorded as {status}.")
    return redirect("dashboard")


@login_required
def family_list(request):
    profiles = FamilyProfile.objects.filter(owner=request.user)
    return render(request, "tracker/family_list.html", {"profiles": profiles})


@login_required
def family_create(request):
    if request.method == "POST":
        form = FamilyProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.owner = request.user
            profile.save()
            messages.success(request, "Family profile added.")
            return redirect("family_list")
    else:
        form = FamilyProfileForm()
    return render(request, "tracker/simple_form.html", {"form": form, "heading": "Add family profile", "back_url": "family_list"})


@login_required
def refill_list(request):
    requests = RefillRequest.objects.filter(owner=request.user).select_related("medicine", "pharmacy")
    pharmacies = Pharmacy.objects.filter(active=True)
    return render(request, "tracker/refill_list.html", {"requests": requests, "pharmacies": pharmacies})


@login_required
def refill_create(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk, owner=request.user)
    if request.method == "POST":
        form = RefillRequestForm(request.POST)
        if form.is_valid():
            refill = form.save(commit=False)
            refill.owner = request.user
            refill.medicine = medicine
            if refill.pharmacy and not refill.pharmacy.active:
                messages.error(request, "This pharmacy is not currently active.")
                return redirect("refill_create", pk=pk)
            refill.save()
            messages.success(request, "Refill request saved locally. It has NOT been sent to a pharmacy.")
            return redirect("refill_list")
    else:
        form = RefillRequestForm()
    form.fields["pharmacy"].queryset = Pharmacy.objects.filter(active=True)
    return render(request, "tracker/simple_form.html", {"form": form, "heading": f"Request refill: {medicine.name}", "back_url": "medicine_list"})


def forgot_password(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        identifier = request.POST.get("identifier", "").strip()
        if not identifier:
            messages.error(request, "Please enter your username or registered email address.")
            return render(request, "registration/forgot_password.html")

        user = User.objects.filter(Q(email__iexact=identifier) | Q(username__iexact=identifier)).first()
        if not user:
            messages.error(request, "No account was found with that username or email address.")
            return render(request, "registration/forgot_password.html", {"identifier": identifier})

        if not user.email:
            messages.error(request, f"User '{user.username}' does not have an email address configured. Please set an email in the admin panel or create a new account.")
            return render(request, "registration/forgot_password.html", {"identifier": identifier})

        otp_record = PasswordResetOTP.generate_otp_for_user(user)
        success, msg = send_password_reset_otp_email(user, otp_record.otp)

        request.session["reset_user_id"] = user.id
        request.session["reset_email"] = user.email
        if success:
            messages.success(request, msg)
        else:
            messages.warning(request, msg)
        return redirect("verify_otp")

    return render(request, "registration/forgot_password.html")


def verify_otp(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    user_id = request.session.get("reset_user_id")
    reset_email = request.session.get("reset_email", "")

    if not user_id:
        messages.error(request, "Please request a password reset code first.")
        return redirect("forgot_password")

    user = User.objects.filter(id=user_id).first()
    if not user:
        messages.error(request, "User session expired. Please start over.")
        return redirect("forgot_password")

    if request.method == "POST":
        entered_otp = request.POST.get("otp", "").strip()
        new_password = request.POST.get("new_password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        if not entered_otp:
            messages.error(request, "Please enter the 6-digit OTP code.")
            return render(request, "registration/verify_otp.html", {"email": reset_email})

        if not new_password or not confirm_password:
            messages.error(request, "Please enter and confirm your new password.")
            return render(request, "registration/verify_otp.html", {"email": reset_email, "otp": entered_otp})

        if new_password != confirm_password:
            messages.error(request, "The passwords you entered do not match.")
            return render(request, "registration/verify_otp.html", {"email": reset_email, "otp": entered_otp})

        if len(new_password) < 4:
            messages.error(request, "Password should be at least 4 characters.")
            return render(request, "registration/verify_otp.html", {"email": reset_email, "otp": entered_otp})

        otp_record = PasswordResetOTP.objects.filter(user=user, otp=entered_otp, is_used=False).first()
        if not otp_record:
            messages.error(request, "Incorrect OTP code. Please check your email and try again.")
            return render(request, "registration/verify_otp.html", {"email": reset_email, "otp": entered_otp})

        if not otp_record.is_valid():
            messages.error(request, "This OTP has expired (10-minute limit). Please request a new code.")
            return redirect("forgot_password")

        user.set_password(new_password)
        user.save()
        otp_record.is_used = True
        otp_record.save()

        request.session.pop("reset_user_id", None)
        request.session.pop("reset_email", None)

        messages.success(request, "Password reset successfully! You can now log in with your new password.")
        return redirect("login")

    return render(request, "registration/verify_otp.html", {"email": reset_email})


@login_required
def scan_prescription(request):
    if request.method != "POST" or "image" not in request.FILES:
        return JsonResponse({"success": False, "error": "Please upload a prescription or medicine image."}, status=400)

    image_file = request.FILES["image"]
    try:
        data = scan_prescription_with_ai(image_file)
        return JsonResponse({"success": True, "data": data})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


