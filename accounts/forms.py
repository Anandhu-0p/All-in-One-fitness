from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

from .models import UserProfile

User = get_user_model()


class EmailAuthenticationForm(AuthenticationForm):
    def clean_username(self):
        identifier = self.cleaned_data['username'].strip()
        if '@' in identifier:
            user = User.objects.filter(email__iexact=identifier).first()
            if user:
                return user.get_username()
        return identifier


class CustomUserRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('A user with this email already exists.')
        return email

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if password:
            validate_password(password, self.instance)
        return password

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError('Passwords do not match.')
        return password2

    def save(self, commit=True):
        from accounts.utils import ROLE_USER, assign_role
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.email = self.cleaned_data['email'].strip().lower()
        if commit:
            user.save()
            assign_role(user, ROLE_USER)
            UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
                    'email': user.email,
                },
            )
        return user


class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    profile_image = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
    )

    class Meta:
        model = UserProfile
        fields = [
            'full_name', 'mobile_number', 'date_of_birth', 'gender', 'profile_image',
            'address', 'fitness_goal', 'activity_level', 'dietary_preference',
            'allergies', 'medical_notes',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. +91 98765 43210'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'profile_image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'fitness_goal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Lose weight, Build muscle'}),
            'activity_level': forms.Select(attrs={'class': 'form-select'}),
            'dietary_preference': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Vegetarian, Vegan, High-protein'}),
            'allergies': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'List any food allergies'}),
            'medical_notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def clean_profile_image(self):
        image = self.cleaned_data.get('profile_image')
        if image:
            if image.size > 2 * 1024 * 1024:
                raise ValidationError('Profile image must be smaller than 2 MB.')
            try:
                FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif', 'webp'])(image)
            except ValidationError as error:
                raise ValidationError(f'invalid file extension: {error.message}') from error
            try:
                from PIL import Image
                Image.open(image).verify()
            except Exception as error:
                raise ValidationError('Upload a valid image file.') from error
        return image

    def clean_mobile_number(self):
        number = self.cleaned_data.get('mobile_number', '').strip()
        if number and not number.replace('+', '', 1).replace(' ', '').replace('-', '').isdigit():
            raise ValidationError('Enter a valid phone number (digits, spaces, + and - only).')
        return number

    def save(self, commit=True):
        profile = super().save(commit=False)
        email = self.cleaned_data.get('email')
        if email:
            email = email.strip().lower()
            if email != profile.user.email:
                existing = User.objects.filter(email__iexact=email).exclude(pk=profile.user.pk)
                if existing.exists():
                    raise ValidationError({'email': 'This email is already in use.'})
                profile.user.email = email
                profile.user.save()
        profile.email = email or profile.user.email
        if commit:
            profile.save()
        return profile


class HealthDetailsForm(forms.ModelForm):
    """User health information: demographics plus current height/weight."""
    height = forms.FloatField(
        required=False, min_value=50, max_value=250,
        label='Height (cm)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
    )
    weight = forms.FloatField(
        required=False, min_value=20, max_value=400,
        label='Weight (kg)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
    )

    class Meta:
        model = UserProfile
        fields = [
            'gender', 'date_of_birth', 'fitness_goal', 'activity_level',
            'dietary_preference', 'allergies', 'medical_notes',
        ]
        widgets = {
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fitness_goal': forms.TextInput(attrs={'class': 'form-control'}),
            'activity_level': forms.Select(attrs={'class': 'form-select'}),
            'dietary_preference': forms.TextInput(attrs={'class': 'form-control'}),
            'allergies': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'medical_notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def save(self, commit=True):
        from users.models import HealthRecord
        profile = super().save(commit=False)
        if commit:
            profile.save()
        height = self.cleaned_data.get('height')
        weight = self.cleaned_data.get('weight')
        if height or weight:
            latest = HealthRecord.objects.filter(user=profile.user).order_by('-recorded_at').first()
            bmi = 0
            if height and weight:
                bmi = round(weight / ((height / 100) ** 2), 1)
            HealthRecord.objects.create(
                user=profile.user,
                height=height or (latest.height if latest else 0),
                weight=weight or (latest.weight if latest else 0),
                bmi=bmi or (latest.bmi if latest else 0),
                body_fat_percentage=latest.body_fat_percentage if latest else 0,
                blood_pressure=latest.blood_pressure if latest else '',
                medical_notes=profile.medical_notes,
                recorded_by=profile.user,
            )
        return profile


class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
    )


class TrainerProfileForm(forms.ModelForm):
    class Meta:
        from trainers.models import TrainerProfile
        model = TrainerProfile
        fields = [
            'full_name', 'mobile_number', 'specialization', 'qualification',
            'experience', 'profile_image', 'bio',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile_number': forms.TextInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Strength & Conditioning'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. ACE Certified PT'}),
            'experience': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'profile_image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }

    def clean_profile_image(self):
        image = self.cleaned_data.get('profile_image')
        if image and image.size > 2 * 1024 * 1024:
            raise ValidationError('Profile image must be smaller than 2 MB.')
        return image


class ExpertProfileForm(forms.ModelForm):
    class Meta:
        from experts.models import ExpertProfile
        model = ExpertProfile
        fields = [
            'full_name', 'mobile_number', 'specialization', 'qualification',
            'profile_image', 'bio',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile_number': forms.TextInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Sports Nutrition'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. MSc Nutrition & Dietetics'}),
            'profile_image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }

    def clean_profile_image(self):
        image = self.cleaned_data.get('profile_image')
        if image and image.size > 2 * 1024 * 1024:
            raise ValidationError('Profile image must be smaller than 2 MB.')
        return image


class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(
        label='Current password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'current-password'}),
    )
    new_password = forms.CharField(
        label='New password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )
    confirm_password = forms.CharField(
        label='Confirm new password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )

    def clean_new_password(self):
        password = self.cleaned_data.get('new_password')
        if password:
            validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        if new_password and confirm_password and new_password != confirm_password:
            self.add_error('confirm_password', 'New passwords do not match.')
        return cleaned_data