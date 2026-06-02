from django.contrib import admin
from .models import Movie, UserProfile, UserVote, VisitorMessage, UserBan


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'director', 'release_date')
    search_fields = ('title', 'director')


@admin.register(UserVote)
class UserVoteAdmin(admin.ModelAdmin):
    # is_approved ve comment alanlarını ekledik
    list_display = ('movie', 'user', 'average_score', 'is_approved')
    list_filter = ('is_approved', 'movie') # Onay durumuna göre filtreleme
    search_fields = ('movie__title', 'user__username', 'comment')
    actions = ['approve_votes', 'disapprove_votes']

    def approve_votes(self, request, queryset):
        queryset.update(is_approved=True)
    approve_votes.short_description = "Seçili yorumları onayla"

    def disapprove_votes(self, request, queryset):
        queryset.update(is_approved=False)
    disapprove_votes.short_description = "Seçili yorumları reddet"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'updated_at')
    search_fields = ('user__username',)


@admin.register(VisitorMessage)
class VisitorMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'is_approved')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('user__username', 'message')
    actions = ['approve_messages', 'disapprove_messages']

    def approve_messages(self, request, queryset):
        queryset.update(is_approved=True)
    approve_messages.short_description = "Seçili mesajları onayla"

    def disapprove_messages(self, request, queryset):
        queryset.update(is_approved=False)
    disapprove_messages.short_description = "Seçili mesajları reddet"


@admin.register(UserBan)
class UserBanAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_indefinite', 'banned_until', 'lifted_at')
    search_fields = ('user__username', 'user__email')
