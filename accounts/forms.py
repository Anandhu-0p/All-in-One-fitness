from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.forms import ModelForm

from .models import UserProfile

User = get_user_model()


class CustomUserRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=[('User', 'User'), ('Trainer', 'Trainer'), ('Expert', 'Expert')], label='Register as')

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError('A user with this email already exists.')
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError('Passwords do not match.')
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
            group, _ = Group.objects.get_or_create(name=self.cleaned_data['role'])
            user.groups.add(group)
            UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
                    'email': user.email or f"{user.username}@example.com",
                },
            )
        return user


class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'full_name', 'mobile_number', 'date_of_birth', 'gender', 'profile_image',
            'address', 'fitness_goal', 'activity_level', 'dietary_preference',
            'allergies', 'medical_notes'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'medical_notes': forms.Textarea(attrs={'rows': 3}),
            'allergies': forms.Textarea(attrs={'rows': 2}),
        }


class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput)
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        if new_password and confirm_password and new_password != confirm_password:
            raise ValidationError('New passwords do not match.')
        return cleaned_data