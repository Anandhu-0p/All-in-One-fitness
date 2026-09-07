from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
	GENDER_CHOICES = [
		('Female', 'Female'),
		('Male', 'Male'),
		('Other', 'Other'),
	]
	ACTIVITY_LEVEL_CHOICES = [
		('Beginner', 'Beginner'),
		('Intermediate', 'Intermediate'),
		('Advanced', 'Advanced'),
	]

	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
	full_name = models.CharField(max_length=150)
	email = models.EmailField()
	mobile_number = models.CharField(max_length=20, blank=True)
	date_of_birth = models.DateField(null=True, blank=True)
	gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
	profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
	address = models.TextField(blank=True)
	fitness_goal = models.CharField(max_length=150, blank=True)
	activity_level = models.CharField(max_length=20, choices=ACTIVITY_LEVEL_CHOICES, blank=True)
	dietary_preference = models.CharField(max_length=100, blank=True)
	allergies = models.TextField(blank=True)
	medical_notes = models.TextField(blank=True)

	def __str__(self):
		return self.full_name or self.user.username
