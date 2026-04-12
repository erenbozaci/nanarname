from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Movie, UserProfile, VisitorMessage


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


class VisitorMessageForm(forms.ModelForm):
    class Meta:
        model = VisitorMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Mesajınızı yazın...'}),
        }


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['description', 'avatar']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Kendiniz hakkında kısa bir tanıtım yazın...'}),
        }


class CustomLoginForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        ban = getattr(user, 'ban', None)
        if ban and ban.lifted_at is None:
            if ban.is_indefinite:
                raise forms.ValidationError(
                    "Hesabınız süresiz olarak yasaklı.",
                    code='inactive',
                )
            if ban.banned_until and ban.banned_until <= timezone.now():
                ban.lifted_at = timezone.now()
                ban.save(update_fields=['lifted_at'])
                user.is_active = True
                user.save(update_fields=['is_active'])
                return
            if ban.banned_until and ban.banned_until > timezone.now():
                raise forms.ValidationError(
                    f"Hesabınız {ban.banned_until.strftime('%d.%m.%Y %H:%M')} tarihine kadar yasaklı.",
                    code='inactive',
                )
        super().confirm_login_allowed(user)
