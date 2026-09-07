from django.contrib.auth.models import User
from django.db import models
from trainers.models import TrainerProfile


class WorkoutPlan(models.Model):
    DIFFICULTY_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    goal = models.CharField(max_length=150, blank=True)
    difficulty_level = models.CharField(max_length=50, choices=DIFFICULTY_CHOICES, default='Beginner')
    duration_weeks = models.PositiveIntegerField(default=4)
    created_by_trainer = models.ForeignKey(TrainerProfile, on_delete=models.CASCADE, related_name='workout_plans')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class WorkoutExercise(models.Model):
    workout_plan = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE, related_name='exercises')
    exercise_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    sets = models.PositiveIntegerField(default=3)
    repetitions = models.PositiveIntegerField(default=10)
    duration = models.CharField(max_length=50, blank=True)
    rest_time = models.CharField(max_length=50, blank=True)
    video_url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.exercise_name


class UserWorkoutAssignment(models.Model):
    workout_plan = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE, related_name='user_assignments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_assignments')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_workouts')
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, default='Active')

    class Meta:
        unique_together = ('workout_plan', 'user')

    def __str__(self):
        return f'{self.user} - {self.workout_plan}'
