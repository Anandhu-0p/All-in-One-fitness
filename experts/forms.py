from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, URLValidator

from .models import DietPlan, DietPlanMeal, FitnessVideo, WellnessTip


class DietPlanForm(forms.ModelForm):
    class Meta:
        model = DietPlan
        fields = ['title', 'description', 'goal', 'calories', 'dietary_preference', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'goal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Fat loss, Muscle gain'}),
            'calories': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'dietary_preference': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Vegetarian, Vegan, High-protein, Gluten-free'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DietMealForm(forms.ModelForm):
    class Meta:
        model = DietPlanMeal
        fields = ['meal_type', 'meal_name', 'description', 'calories', 'order']
        widgets = {
            'meal_type': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('Breakfast', 'Breakfast'), ('Lunch', 'Lunch'), ('Dinner', 'Dinner'),
                ('Snack', 'Snack'), ('Pre-workout', 'Pre-workout'), ('Post-workout', 'Post-workout'),
            ]),
            'meal_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'calories': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }


DietMealFormSet = forms.inlineformset_factory(
    DietPlan, DietPlanMeal, form=DietMealForm, extra=3, can_delete=True
)


class FitnessVideoForm(forms.ModelForm):
    class Meta:
        model = FitnessVideo
        fields = ['title', 'description', 'category', 'thumbnail', 'video_url', 'uploaded_file', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Strength, Yoga, Cardio, Motivation'}),
            'thumbnail': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://www.youtube.com/watch?v=…'}),
            'uploaded_file': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'video/*'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned = super().clean()
        video_url = cleaned.get('video_url')
        uploaded_file = cleaned.get('uploaded_file')
        if not video_url and not uploaded_file:
            raise ValidationError('Provide either a video URL or upload a video file.')
        if video_url:
            URLValidator()(video_url)
        return cleaned

    def clean_thumbnail(self):
        thumb = self.cleaned_data.get('thumbnail')
        if thumb:
            if thumb.size > 2 * 1024 * 1024:
                raise ValidationError('Thumbnail must be smaller than 2 MB.')
            try:
                FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif', 'webp'])(thumb)
            except ValidationError as error:
                raise ValidationError(f'invalid file extension: {error.message}') from error
        return thumb

    def clean_uploaded_file(self):
        file = self.cleaned_data.get('uploaded_file')
        if file:
            if file.size > 100 * 1024 * 1024:
                raise ValidationError('Video file must be smaller than 100 MB.')
            try:
                FileExtensionValidator(['mp4', 'webm', 'ogg', 'mov', 'avi', 'mkv'])(file)
            except ValidationError as error:
                raise ValidationError(f'Invalid file extension: {error.message}') from error
        return file


class WellnessTipForm(forms.ModelForm):
    class Meta:
        model = WellnessTip
        fields = ['title', 'content', 'category', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Nutrition, Mental health, Sleep, Lifestyle'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }