from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, Count
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

# FİLM VE İÇERİK YÖNETİMİ
class Movie(models.Model):
    """
    Sistemdeki filmlerin temel veritabanı tablosu.
    Hem adminlerin girdiği profesyonel puanları hem de kullanıcıların verdiği puanları tutar.
    """
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    director = models.CharField(max_length=150, blank=True)
    image_url = models.URLField(blank=True)
    release_date = models.DateField()

# Adminlerin (Editörlerin) film için belirlediği alt kategori puanları (0-100 arası)
    score_scenario = models.PositiveSmallIntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    score_acting = models.PositiveSmallIntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    score_visuals = models.PositiveSmallIntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    score_sound = models.PositiveSmallIntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    score_editing = models.PositiveSmallIntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    class Meta:
        ordering = ['-release_date', 'title']

    def __str__(self):
        return self.title

    @property
    def admin_score(self):
        # Admin puanlarının genel ortalamasını dinamik olarak hesaplar
        return (
            self.score_scenario
            + self.score_acting
            + self.score_visuals
            + self.score_sound
            + self.score_editing
        ) / 5.0

    def user_vote_stats(self):
        # Veritabanını yormadan (aggregate ile) tüm kullanıcı oylarının ortalamasını tek seferde çeker
        stats = self.user_votes.aggregate(
            vote_count=Count('id'),
            user_avg_scenario=Avg('score_scenario'),
            user_avg_acting=Avg('score_acting'),
            user_avg_visuals=Avg('score_visuals'),
            user_avg_sound=Avg('score_sound'),
            user_avg_editing=Avg('score_editing'),
        )
        stats['vote_count'] = stats['vote_count'] or 0
        stats['user_avg_scenario'] = stats['user_avg_scenario'] or 0
        stats['user_avg_acting'] = stats['user_avg_acting'] or 0
        stats['user_avg_visuals'] = stats['user_avg_visuals'] or 0
        stats['user_avg_sound'] = stats['user_avg_sound'] or 0
        stats['user_avg_editing'] = stats['user_avg_editing'] or 0
        return stats

    def user_score(self, stats=None):
        # Kullanıcıların verdiği puanların nihai ortalamasını döndürür
        stats = stats or self.user_vote_stats()
        if stats['vote_count'] == 0:
            return 0
        return (
            stats['user_avg_scenario']
            + stats['user_avg_acting']
            + stats['user_avg_visuals']
            + stats['user_avg_sound']
            + stats['user_avg_editing']
        ) / 5.0

    def cacik_score(self, stats=None):
        # Sitenin ana algoritması: Admin ve Kullanıcı puanlarını harmanlayarak filmin genel 'Cacık' skorunu belirler.
        stats = stats or self.user_vote_stats()
        user_score = self.user_score(stats)
        if stats['vote_count'] == 0 and self.admin_score == 0:
            return -1
        if stats['vote_count'] == 0:
            return self.admin_score
        if self.admin_score == 0:
            return user_score
        return (self.admin_score + user_score) / 2.0


# KULLANICI ETKİLEŞİMİ VE YAPAY ZEKA KONTROLÜ
class UserVote(models.Model):
    """
    Kullanıcıların filmlere yaptığı yorumları ve verdiği puanları tutan model.
    Burası NLP tabanlı Toksisite modelimizin (Akıllı Sansür) doğrudan denetim yaptığı kritik tablodur.
    """
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='user_votes')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='movie_votes'
    )
    score_scenario = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    score_acting = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    score_visuals = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    score_sound = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    score_editing = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    comment = models.TextField(blank=True)

# Orijinal koddaki tekrarlı alanlar (Kod yapısı bozulmaması için aynen bırakıldı)
    score_editing = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    comment = models.TextField(blank=True)

   # YENİ EKLENEN ALAN: Varsayılan olarak True, sadece toksikse False yapacağız
    # Yapay zeka modelimiz bu metni analiz eder; eğer siber zorbalık/toksisite eşiği (0.18) aşılırsa 
    # bu bayrak False çekilir ve yorum sistemde gizlenir/filtrelenir.
    is_approved = models.BooleanField(default=True, verbose_name="Onaylandı mı?")

    class Meta:
        constraints = [
            # Bir kullanıcının bir filme yalnızca bir kez oy verebilmesini sağlayan kısıtlama
            models.UniqueConstraint(fields=['movie', 'user'], name='unique_movie_vote_per_user')
        ]

    @property
    def average_score(self):
        return (
            self.score_scenario
            + self.score_acting
            + self.score_visuals
            + self.score_sound
            + self.score_editing
        ) / 5.0


# KULLANICI PROFİLİ VE CEZA (BAN) SİSTEMİ
class UserProfile(models.Model):
    """
    Django'nun varsayılan User modelini genişleterek ekstra profil detayları (avatar vb.) ekler.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    description = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Kullanıcı Profili'
        verbose_name_plural = 'Kullanıcı Profilleri'

    def __str__(self):
        return f'{self.user.username} profili'


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    # Yeni bir kullanıcı kayıt olduğunda otomatik olarak boş bir UserProfile oluşturur (Signal)
    if created:
        UserProfile.objects.create(user=instance)


class UserBan(models.Model):
    """
    Yapay zeka (Akıllı Sansür) tarafından sürekli toksik içerik ürettiği tespit edilen
    kullanıcıların platformdan uzaklaştırılmasını yöneten ceza modülü.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ban',
    )
    is_indefinite = models.BooleanField(default=False)# Süresiz ban kontrolü
    banned_until = models.DateTimeField(null=True, blank=True)# Süreli ban kontrolü
    created_at = models.DateTimeField(auto_now_add=True)
    lifted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.is_indefinite:
            return f"{self.user.username} - Süresiz yasak"
        return f"{self.user.username} - {self.banned_until:%d.%m.%Y %H:%M}" if self.banned_until else f"{self.user.username} - Ban"

    @property
    def is_active(self):
        # Cezanın anlık olarak devam edip etmediğini matematiksel/zamansal olarak doğrular
        if self.lifted_at is not None:
            return False
        if self.is_indefinite:
            return True
        return self.banned_until is not None and self.banned_until > timezone.now()


class VisitorMessage(models.Model):
    """
    Ziyaretçi mesajlarını tutan genel model.
    Bu model de aynı şekilde NLP modelinin denetimine tabi tutularak onay sürecinden (is_approved) geçer.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='visitor_messages'
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.message[:50]}..."
