from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, Count


class Movie(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    director = models.CharField(max_length=150, blank=True)
    image_url = models.URLField(blank=True)
    release_date = models.DateField()

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
        return (
            self.score_scenario
            + self.score_acting
            + self.score_visuals
            + self.score_sound
            + self.score_editing
        ) / 5.0

    def user_vote_stats(self):
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
        stats = stats or self.user_vote_stats()
        user_score = self.user_score(stats)
        if stats['vote_count'] == 0 and self.admin_score == 0:
            return -1
        if stats['vote_count'] == 0:
            return self.admin_score
        if self.admin_score == 0:
            return user_score
        return (self.admin_score + user_score) / 2.0


class UserVote(models.Model):
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

    class Meta:
        constraints = [
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
