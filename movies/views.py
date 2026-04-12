from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group, User
from django.db.models import Avg, Count, Prefetch
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import MovieForm, UserRegistrationForm, VoteForm
from .models import Movie, UserVote


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

        movie.admin_score = (
            movie.score_scenario
            + movie.score_acting
            + movie.score_visuals
            + movie.score_sound
            + movie.score_editing
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


@user_passes_test(is_admin)
def users_index(request):
    users = User.objects.order_by('username')
    return render(request, 'users/index.html', {'users': users})


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
