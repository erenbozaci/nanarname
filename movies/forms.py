from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Movie, UserProfile, VisitorMessage

# İÇERİK VE FİLM YÖNETİM FORMLARI
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

# KULLANICI ETKİLEŞİMİ VE NLP VERİ GİRİŞ FORMLARI
class VoteForm(forms.Form):
    """
    Kullanıcıların filmlere puan verip yorum yaptığı ana form.
    DİKKAT: Buradaki 'comment' (yorum) alanı, arka planda çalışan (views.py) BERT tabanlı 
    doğal dil işleme (NLP) modelimizin analiz edeceği ham metni toplar.
    """
    sScenario = forms.IntegerField(min_value=0, max_value=100, initial=50)
    sActing = forms.IntegerField(min_value=0, max_value=100, initial=50)
    sVisuals = forms.IntegerField(min_value=0, max_value=100, initial=50)
    sSound = forms.IntegerField(min_value=0, max_value=100, initial=50)
    sEditing = forms.IntegerField(min_value=0, max_value=100, initial=50)
    comment = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))


class VisitorMessageForm(forms.ModelForm):
    """
    Ziyaretçi defterine bırakılan mesajları toplayan form.
    Bu alandan gelen veriler de moderasyon (Akıllı Sansür) sürecinden geçirilmektedir.
    """
    class Meta:
        model = VisitorMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Mesajınızı yazın...'}),
        }

# KULLANICI KAYIT VE PROFİL FORMLARI
class UserRegistrationForm(UserCreationForm):
    """
    Yeni kullanıcıların sisteme kayıt olurken kullandığı standart doğrulama formu.
    """
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')


class UserProfileForm(forms.ModelForm):
    """
    Kullanıcıların kişisel profil detaylarını ve avatarlarını güncellediği form.
    """
    class Meta:
        model = UserProfile
        fields = ['description', 'avatar']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Kendiniz hakkında kısa bir tanıtım yazın...'}),
        }

# GÜVENLİK VE CEZA (BAN) KONTROLLÜ GİRİŞ FORMU
class CustomLoginForm(AuthenticationForm):
    """
    Django'nun standart giriş formunu ezerek (override) özel ceza kontrolü eklediğimiz sınıf.
    Siber zorbalık veya toksisite sebebiyle NLP modelimizin tespiti sonucu banlanan 
    kullanıcıların sisteme giriş denemeleri burada engellenir.
    """
    def confirm_login_allowed(self, user):
        ban = getattr(user, 'ban', None)
        # Eğer kullanıcının aktif bir cezası varsa
        if ban and ban.lifted_at is None:
            # 1. Durum: Süresiz Yasaklama Kontrolü
            if ban.is_indefinite:
                raise forms.ValidationError(
                    "Hesabınız süresiz olarak yasaklı.",
                    code='inactive',
                )
            # 2. Durum: Süreli Yasaklamanın Bitiş Kontrolü (Ceza süresi dolmuşsa ban kaldırılır)
            if ban.banned_until and ban.banned_until <= timezone.now():
                ban.lifted_at = timezone.now()
                ban.save(update_fields=['lifted_at'])
                user.is_active = True
                user.save(update_fields=['is_active'])
                return
            
            # 3. Durum: Süreli Yasaklamanın Devam Etmesi (Giriş reddedilir)
            if ban.banned_until and ban.banned_until > timezone.now():
                raise forms.ValidationError(
                    f"Hesabınız {ban.banned_until.strftime('%d.%m.%Y %H:%M')} tarihine kadar yasaklı.",
                    code='inactive',
                )
        # Herhangi bir ceza yoksa standart giriş işlemine devam et
        super().confirm_login_allowed(user)
