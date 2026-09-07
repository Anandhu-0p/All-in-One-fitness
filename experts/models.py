from django.contrib.auth.models import User
from django.db import models


class ExpertProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='expert_profile')
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    mobile_number = models.CharField(max_length=20, blank=True)
    specialization = models.CharField(max_length=150, blank=True)
    qualification = models.CharField(max_length=150, blank=True)
    profile_image = models.ImageField(upload_to='experts/', blank=True, null=True)
    bio = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.full_name


class DietPlan(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    goal = models.CharField(max_length=150, blank=True)
    calories = models.IntegerField(default=0)
    dietary_preference = models.CharField(max_length=100, blank=True)
    created_by_expert = models.ForeignKey(ExpertProfile, on_delete=models.CASCADE, related_name='diet_plans')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class DietPlanMeal(models.Model):
    diet_plan = models.ForeignKey(DietPlan, on_delete=models.CASCADE, related_name='meals')
    meal_type = models.CharField(max_length=50)
    meal_name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    calories = models.IntegerField(default=0)
    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'{self.meal_type}: {self.meal_name}'


class UserDietAssignment(models.Model):
    diet_plan = models.ForeignKey(DietPlan, on_delete=models.CASCADE, related_name='assigned_users')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='diet_assignments')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_diets')
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, default='Active')

    class Meta:
        unique_together = ('diet_plan', 'user')


class FitnessVideo(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=80, blank=True)
    thumbnail = models.ImageField(upload_to='videos/thumbnails/', blank=True, null=True)
    video_url = models.URLField(blank=True)
    uploaded_file = models.FileField(upload_to='videos/uploads/', blank=True, null=True)
    uploaded_by_expert = models.ForeignKey(ExpertProfile, on_delete=models.CASCADE, related_name='uploaded_videos')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class WellnessTip(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=80, blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=True)

    def __str__(self):
        return self.title
