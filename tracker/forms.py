from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Medicine, FamilyProfile, RefillRequest


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")


class MedicineForm(forms.ModelForm):
    schedule_times = forms.CharField(
        required=False,
        help_text="24-hour times separated by commas, e.g. 08:00, 20:00",
        widget=forms.TextInput(attrs={"placeholder": "08:00, 20:00"}),
    )
    class Meta:
        model = Medicine
        fields = [
            "profile", "name", "strength", "instructions", "unit", "stock_quantity",
            "daily_usage", "refill_notice_days", "expiry_date", "pharmacy_link", "notes", "schedule_times"
        ]
        widgets = {"expiry_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields["profile"].queryset = FamilyProfile.objects.filter(owner=self.user)
        self.fields["profile"].required = False

    def clean_schedule_times(self):
        raw = self.cleaned_data.get("schedule_times", "")
        result = []
        for item in raw.split(","):
            item = item.strip()
            if not item:
                continue
            try:
                hour, minute = item.split(":")
                hour, minute = int(hour), int(minute)
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError
                value = f"{hour:02d}:{minute:02d}"
                if value not in result:
                    result.append(value)
            except (ValueError, TypeError):
                raise forms.ValidationError("Use 24-hour time format like 08:00, 20:00.")
        return result


class FamilyProfileForm(forms.ModelForm):
    class Meta:
        model = FamilyProfile
        fields = ["name", "relationship"]


class RefillRequestForm(forms.ModelForm):
    class Meta:
        model = RefillRequest
        fields = ["pharmacy", "quantity_requested", "notes"]
        widgets = {"notes": forms.TextInput(attrs={"placeholder": "Optional note to the pharmacy"})}
