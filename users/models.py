from django.contrib.auth.models import User
from django.db import models


class HealthRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='health_records')
    height = models.FloatField(default=0)
    weight = models.FloatField(default=0)
    bmi = models.FloatField(default=0)
    body_fat_percentage = models.FloatField(default=0)
    blood_pressure = models.CharField(max_length=50, blank=True)
    medical_notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='recorded_health_data')
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} health record'


class ProgressRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress_records')
    weight = models.FloatField(default=0)
    waist_measurement = models.FloatField(default=0)
    body_fat_percentage = models.FloatField(default=0)
    progress_note = models.TextField(blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} progress on {self.recorded_at.date()}'
