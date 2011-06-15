from django.forms.models import ModelForm
from models import FaqEntry
from django import forms


class FaqEntryForm(ModelForm):
    body = forms.CharField()
    
    class Meta:
        model = FaqEntry
        exclude = ('page', 'position', 'placeholder', 'language', 'plugin_type')
