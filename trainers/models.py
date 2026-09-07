from django.contrib.auth.models import User
from django.db import models


class TrainerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='trainer_profile')
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    mobile_number = models.CharField(max_length=20, blank=True)
    specialization = models.CharField(max_length=150, blank=True)
    qualification = models.CharField(max_length=150, blank=True)
    experience = models.PositiveIntegerField(default=0)
    profile_image = models.ImageField(upload_to='trainers/', blank=True, null=True)
    bio = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.full_name


class Batch(models.Model):
    STATUS_CHOICES = [('Active', 'Active'), ('Upcoming', 'Upcoming'), ('Closed', 'Closed')]
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    schedule = models.CharField(max_length=200, blank=True)
    capacity = models.PositiveIntegerField(default=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class BatchMembership(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='batch_memberships')
    joined_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Active')

    class Meta:
        unique_together = ('batch', 'user')

    def __str__(self):
        return f'{self.user} in {self.batch}'


class TrainerAssignment(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='trainer_assignments')
    trainer = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE, related_name='assigned_batches')
    assigned_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Active')

    class Meta:
        unique_together = ('batch', 'trainer')

    def __str__(self):
        return f'{self.trainer} -> {self.batch}'


class Attendance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_entries')
    trainer = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE, related_name='attendance_records')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField()
    status = models.CharField(max_length=20, default='Present')
    notes = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'batch', 'date'],
                name='unique_attendance_per_user_batch_date',
            ),
        ]

    def __str__(self):
        return f'{self.user} - {self.date} - {self.status}'
