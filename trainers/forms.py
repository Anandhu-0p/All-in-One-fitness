from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from fitness.models import WorkoutExercise, WorkoutPlan
from trainers.models import Batch
from users.models import HealthRecord, ProgressRecord


class WorkoutPlanForm(forms.ModelForm):
    class Meta:
        model = WorkoutPlan
        fields = ['title', 'description', 'goal', 'difficulty_level', 'duration_weeks', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'goal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Fat loss, Muscle gain, Endurance'}),
            'difficulty_level': forms.Select(attrs={'class': 'form-select'}),
            'duration_weeks': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class WorkoutExerciseForm(forms.ModelForm):
    class Meta:
        model = WorkoutExercise
        fields = ['exercise_name', 'description', 'sets', 'repetitions', 'duration', 'rest_time', 'video_url', 'order']
        widgets = {
            'exercise_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'sets': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'repetitions': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'duration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 45 seconds'}),
            'rest_time': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 60 seconds'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://…'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            for field_name in self.fields:
                self.fields[field_name].required = False

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('exercise_name'):
            return {}
        return cleaned

    def clean_video_url(self):
        url = self.cleaned_data.get('video_url')
        if url:
            URLValidator()(url)
        return url


class WorkoutExerciseFormSet(forms.BaseInlineFormSet):
    def save(self, commit=True):
        instances = []
        self.new_objects = []
        self.changed_objects = []
        self.deleted_objects = []
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                if form.instance.pk:
                    self.deleted_objects.append(form.instance)
                    if commit:
                        form.instance.delete()
                continue
            if not form.cleaned_data.get('exercise_name'):
                continue
            instance = form.save(commit=False)
            instance.workout_plan = self.instance
            if form.instance.pk:
                self.changed_objects.append((instance, form.changed_data))
            else:
                self.new_objects.append(instance)
            if commit:
                instance.save()
            instances.append(instance)
        return instances


ExerciseFormSet = forms.inlineformset_factory(
    WorkoutPlan, WorkoutExercise, form=WorkoutExerciseForm, formset=WorkoutExerciseFormSet,
    extra=3, can_delete=True,
)


class HealthRecordForm(forms.ModelForm):
    bmi = forms.FloatField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'readonly': True}))
    body_fat_percentage = forms.FloatField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}))

    class Meta:
        model = HealthRecord
        fields = ['height', 'weight', 'bmi', 'body_fat_percentage', 'blood_pressure', 'medical_notes']
        widgets = {
            'height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': 50, 'max': 250}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': 20, 'max': 400}),
            'bmi': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'readonly': True}),
            'body_fat_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'blood_pressure': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 120/80'}),
            'medical_notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def clean(self):
        cleaned = super().clean()
        height = cleaned.get('height')
        weight = cleaned.get('weight')
        if height and weight:
            cleaned['bmi'] = round(weight / ((height / 100) ** 2), 1)
        return cleaned


class ProgressRecordForm(forms.ModelForm):
    class Meta:
        model = ProgressRecord
        fields = ['weight', 'waist_measurement', 'body_fat_percentage', 'progress_note']
        widgets = {
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': 20, 'max': 400}),
            'waist_measurement': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'body_fat_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'progress_note': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


class WorkoutAssignmentForm(forms.Form):
    """Assign a workout plan to an individual user or to an entire batch."""
    target_type = forms.ChoiceField(
        choices=[('user', 'Individual user'), ('batch', 'Whole batch')],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Assign to',
    )
    user = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        empty_label='Select a user…',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='User',
    )
    batch = forms.ModelChoiceField(
        queryset=Batch.objects.none(),
        required=False,
        empty_label='Select a batch…',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Batch',
    )

    def __init__(self, *args, **kwargs):
        self.user_qs = kwargs.pop('user_qs', None)
        self.batch_qs = kwargs.pop('batch_qs', None)
        super().__init__(*args, **kwargs)
        if self.user_qs is not None:
            self.fields['user'].queryset = self.user_qs
        if self.batch_qs is not None:
            self.fields['batch'].queryset = self.batch_qs

    def clean(self):
        cleaned = super().clean()
        target_type = cleaned.get('target_type')
        if target_type == 'user' and not cleaned.get('user'):
            raise ValidationError('Select a user to assign the plan to.')
        if target_type == 'batch' and not cleaned.get('batch'):
            raise ValidationError('Select a batch to assign the plan to.')
        return cleaned