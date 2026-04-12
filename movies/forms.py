from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Movie


class MovieForm(forms.ModelForm):
    class Meta:
        model = Movie
        fields = [
            'title',
            'description',
            'director',
            'image_url',
            'release_date',
            'score_scenario',
            'score_acting',
            'score_visuals',
            'score_sound',
            'score_editing',
        ]
        widgets = {
            'release_date': forms.DateInput(attrs={'type': 'date'}),
        }


class VoteForm(forms.Form):
    sScenario = forms.IntegerField(min_value=0, max_value=100, initial=50)
    sActing = forms.IntegerField(min_value=0, max_value=100, initial=50)
    sVisuals = forms.IntegerField(min_value=0, max_value=100, initial=50)
    sSound = forms.IntegerField(min_value=0, max_value=100, initial=50)
    sEditing = forms.IntegerField(min_value=0, max_value=100, initial=50)
    comment = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')
