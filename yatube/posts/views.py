from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from users.forms import User

from .forms import PostForm, CommentForm
from .models import Group, Post, Follow
from .utils import paginator


def index(request):
    post_list = Post.objects.order_by('pub_date').select_related(
        'group', 'author'
    ).all()
    page_obj = paginator(request, post_list)
    return render(request, 'posts/index.html', {'page_obj': page_obj})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author').all()
    page_obj = paginator(request, post_list)
    return render(request, 'posts/group_list.html', {
        'group': group,
        'page_obj': page_obj
    })


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('group').all()
    page_obj = paginator(request, post_list)
    following = []
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user)
    return render(request, 'posts/profile.html', {
        'username': author,
        'page_obj': page_obj,
        'following': following,
        'author': author
    })


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm()
    comments = post.comments.all()
    return render(request,
                  'posts/post_detail.html',
                  {'post': post, 'form': form, 'comments': comments})


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()
        return redirect('posts:profile', request.user)
    return render(request, 'posts/post_create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post_id and request.user != post.author:
        return redirect("posts:profile", post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id)
    return render(request, 'posts/post_create.html', {
        'form': form,
        'is_edit': True
    })


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    following = Follow.objects.filter(user=request.user).values('author')
    posts_list = Post.objects.filter(
        author__in=following).order_by('pub_date').select_related(
        'group', 'author'
    ).all()
    page_obj = paginator(request, posts_list)
    return render(request, 'posts/follow.html', {'page_obj': page_obj})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    following = Follow.objects.filter(user=request.user)
    if request.user != author:
        following.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', author)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    following = Follow.objects.get(user=request.user, author=author)
    if request.user != author:
        following.delete()
    return redirect('posts:profile', author)
