from django.contrib import admin
from .models import Movie, UserVote, VisitorMessage, UserBan


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'director', 'release_date')
    search_fields = ('title', 'director')


@admin.register(UserVote)
class UserVoteAdmin(admin.ModelAdmin):
    list_display = ('movie', 'user', 'average_score')
    search_fields = ('movie__title', 'user__username')


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
