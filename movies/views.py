from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group, User
from django.db.models import Avg, Count, Prefetch, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from datetime import timedelta

from .forms import MovieForm, UserRegistrationForm, UserProfileForm, VoteForm, VisitorMessageForm
from .models import Movie, UserProfile, UserVote, VisitorMessage, UserBan


def is_admin(user):
    return user.is_authenticated and user.is_staff


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('movies:index')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


def index(request):
    movies = Movie.objects.annotate(
        vote_count=Count('user_votes'),
        user_avg_scenario=Avg('user_votes__score_scenario'),
        user_avg_acting=Avg('user_votes__score_acting'),
        user_avg_visuals=Avg('user_votes__score_visuals'),
        user_avg_sound=Avg('user_votes__score_sound'),
        user_avg_editing=Avg('user_votes__score_editing'),
    )

    for movie in movies:
        movie.user_avg_scenario = movie.user_avg_scenario or 0
        movie.user_avg_acting = movie.user_avg_acting or 0
        movie.user_avg_visuals = movie.user_avg_visuals or 0
        movie.user_avg_sound = movie.user_avg_sound or 0
        movie.user_avg_editing = movie.user_avg_editing or 0
        movie.user_score = 0
        if movie.vote_count > 0:
            movie.user_score = (
                movie.user_avg_scenario
                + movie.user_avg_acting
                + movie.user_avg_visuals
                + movie.user_avg_sound
                + movie.user_avg_editing
            ) / 5.0

        if movie.vote_count == 0 and movie.admin_score == 0:
            movie.cacik_score = -1
        elif movie.vote_count == 0:
            movie.cacik_score = movie.admin_score
        elif movie.admin_score == 0:
            movie.cacik_score = movie.user_score
        else:
            movie.cacik_score = (movie.admin_score + movie.user_score) / 2.0

    return render(request, 'movies/index.html', {'movies': movies})


def details(request, pk):
    movie = get_object_or_404(
        Movie.objects.prefetch_related(Prefetch('user_votes', queryset=UserVote.objects.select_related('user'))),
        pk=pk,
    )
    comments = movie.user_votes.exclude(comment='').order_by('-id')
    for vote in comments:
        if not hasattr(vote.user, 'profile'):
            UserProfile.objects.get_or_create(user=vote.user)
    stats = movie.user_vote_stats()
    context = {
        'movie': movie,
        'comments': comments,
        'stats': stats,
        'user_score': movie.user_score(stats),
        'cacik_score': movie.cacik_score(stats),
        'vote_form': VoteForm(),
    }
    return render(request, 'movies/details.html', context)


@user_passes_test(is_admin)
def create_movie(request):
    if request.method == 'POST':
        form = MovieForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('movies:index')
    else:
        form = MovieForm()
    return render(request, 'movies/form.html', {'form': form, 'page_title': 'Yeni Film Ekle'})


@user_passes_test(is_admin)
def edit_movie(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    if request.method == 'POST':
        form = MovieForm(request.POST, instance=movie)
        if form.is_valid():
            form.save()
            return redirect('movies:details', pk=movie.pk)
    else:
        form = MovieForm(instance=movie)
    return render(
        request, 'movies/form.html', {'form': form, 'movie': movie, 'page_title': 'Filmi Düzenle'}
    )


@user_passes_test(is_admin)
def delete_movie(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    if request.method == 'POST':
        movie.delete()
        return redirect('movies:index')
    return render(request, 'movies/delete.html', {'movie': movie})


@login_required
def vote(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    if request.method != 'POST':
        return HttpResponseForbidden()
    form = VoteForm(request.POST)
    if form.is_valid():
        UserVote.objects.update_or_create(
            movie=movie,
            user=request.user,
            defaults={
                'score_scenario': form.cleaned_data['sScenario'],
                'score_acting': form.cleaned_data['sActing'],
                'score_visuals': form.cleaned_data['sVisuals'],
                'score_sound': form.cleaned_data['sSound'],
                'score_editing': form.cleaned_data['sEditing'],
                'comment': form.cleaned_data['comment'],
            },
        )
    return redirect('movies:details', pk=movie.pk)


def refresh_user_ban_status(user):
    ban = getattr(user, 'ban', None)
    if not ban or ban.lifted_at is not None:
        return
    if ban.is_indefinite:
        return
    if ban.banned_until and ban.banned_until <= timezone.now():
        ban.lifted_at = timezone.now()
        ban.save(update_fields=['lifted_at'])
        user.is_active = True
        user.save(update_fields=['is_active'])


@user_passes_test(is_admin)
def users_index(request):
    users = User.objects.order_by('username').select_related('ban')
    for u in users:
        refresh_user_ban_status(u)
    return render(request, 'users/index.html', {'users': users})


@user_passes_test(is_admin)
def manage_user(request, user_id):
    if request.method != 'POST':
        return HttpResponseForbidden()
    target_user = get_object_or_404(User, pk=user_id)
    if target_user == request.user:
        return redirect('movies:users_index')

    action = request.POST.get('action')
    if action == 'ban_temp':
        try:
            days = int(request.POST.get('ban_days', 0))
        except (TypeError, ValueError):
            days = 0
        if days > 0:
            ban_until = timezone.now() + timedelta(days=days)
            UserBan.objects.update_or_create(
                user=target_user,
                defaults={
                    'is_indefinite': False,
                    'banned_until': ban_until,
                    'lifted_at': None,
                },
            )
            target_user.is_active = False
            target_user.save(update_fields=['is_active'])
    elif action == 'ban_indef':
        UserBan.objects.update_or_create(
            user=target_user,
            defaults={
                'is_indefinite': True,
                'banned_until': None,
                'lifted_at': None,
            },
        )
        target_user.is_active = False
        target_user.save(update_fields=['is_active'])
    elif action == 'lift':
        ban = getattr(target_user, 'ban', None)
        if ban and ban.lifted_at is None:
            ban.lifted_at = timezone.now()
            ban.save(update_fields=['lifted_at'])
        target_user.is_active = True
        target_user.save(update_fields=['is_active'])
    elif action == 'delete':
        target_user.delete()
    return redirect('movies:users_index')


@user_passes_test(is_admin)
def toggle_admin(request, user_id):
    if request.method != 'POST':
        return HttpResponseForbidden()
    target_user = get_object_or_404(User, pk=user_id)
    if target_user == request.user:
        return redirect('movies:users_index')

    admin_group, _ = Group.objects.get_or_create(name='Admin')
    if target_user.groups.filter(name='Admin').exists():
        target_user.groups.remove(admin_group)
        if not target_user.is_superuser:
            target_user.is_staff = False
    else:
        target_user.groups.add(admin_group)
        target_user.is_staff = True
    target_user.save(update_fields=['is_staff'])
    return redirect('movies:users_index')


@login_required
def user_profile(request, user_id):
    profile_user = get_object_or_404(User, pk=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=profile_user)
    movie_comments = UserVote.objects.select_related('movie').filter(
        user=profile_user,
    ).exclude(comment='').order_by('-id')
    if request.user == profile_user:
        visitor_messages = VisitorMessage.objects.filter(user=profile_user).order_by('-created_at')
    else:
        visitor_messages = VisitorMessage.objects.filter(user=profile_user, is_approved=True).order_by('-created_at')
    return render(request, 'users/profile.html', {
        'profile_user': profile_user,
        'profile': profile,
        'movie_comments': movie_comments,
        'visitor_messages': visitor_messages,
    })


@login_required
def edit_profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('movies:user_profile', user_id=request.user.id)
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'users/edit_profile.html', {
        'form': form,
        'profile': profile,
    })


@login_required
def visitors_book(request):
    messages = VisitorMessage.objects.filter(
        Q(is_approved=True) | Q(user=request.user)
    ).order_by('-created_at')[:10]
    if request.method == 'POST':
        form = VisitorMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.user = request.user
            message.save()
            return redirect('movies:visitors_book')
    else:
        form = VisitorMessageForm()
    return render(request, 'movies/visitors_book.html', {
        'messages': messages,
        'form': form
    })
