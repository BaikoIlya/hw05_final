from django.contrib.auth.models import AnonymousUser
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from functools import wraps
from .forms import PostForm, CommentForm
from .models import Post, Group, Follow


User = get_user_model()


def edit_rights(func):
    @wraps(func)
    def check_author(request, post_id):
        post = Post.objects.get(pk=post_id)
        if request.user == post.author:
            return func(request, post_id)
        return redirect(f'/posts/{post_id}')
    return check_author


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all().select_related('author')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    auth = User.objects.get(username=username)
    post_list = Post.objects.filter(author=auth.pk)
    cnt = post_list.count()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=auth
        ).exists()
    else:
        following = False
    context = {
        'cnt': cnt,
        'page_obj': page_obj,
        'auth': auth,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = Post.objects.get(pk=post_id)
    form = CommentForm()
    comments = post.comments.all().select_related('author')
    cnt = Post.objects.filter(author=post.author).count()
    context = {
        'post': post,
        'cnt': cnt,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        instance = form.save(commit=False)
        instance.author = request.user
        instance.save()
        return redirect(f'/profile/{request.user.username}/')
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
@edit_rights
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if form.is_valid():
        form.save()
        return redirect(f'/posts/{post_id}')
    context = {
        'form': form,
        'post': post,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = Post.objects.get(pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    users_followings = Follow.objects.filter(user=request.user)
    follows_list = []
    for follows in users_followings:
        follows_list.append(follows.author.id)
    post_list = Post.objects.filter(author__in=follows_list)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    if Follow.objects.filter(
            user=request.user,
            author=User.objects.get(username=username)
    ).exists():
        return profile(request, username)
    if request.user == User.objects.get(username=username):
        return profile(request, username)
    else:
        Follow.objects.create(
            user=request.user,
            author=User.objects.get(username=username)
        )
    return profile(request, username)


@login_required
def profile_unfollow(request, username):
    del_follow = Follow.objects.filter(
        user=request.user,
        author=User.objects.get(username=username)
    )
    del_follow.delete()
    return profile(request, username)
