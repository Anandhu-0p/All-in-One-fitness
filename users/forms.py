from django import forms

from .models import ProgressRecord


class ProgressEntryForm(forms.ModelForm):
    class Meta:
        model = ProgressRecord
        fields = ['weight', 'waist_measurement', 'body_fat_percentage', 'progress_note']
        widgets = {
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': 20, 'max': 400}),
            'waist_measurement': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'body_fat_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'progress_note': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }