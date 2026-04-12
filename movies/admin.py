from django.contrib import admin
from .models import Movie, UserVote


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'director', 'release_date')
    search_fields = ('title', 'director')


@admin.register(UserVote)
class UserVoteAdmin(admin.ModelAdmin):
    list_display = ('movie', 'user', 'average_score')
    search_fields = ('movie__title', 'user__username')
