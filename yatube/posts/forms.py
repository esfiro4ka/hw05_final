from django import forms

from .models import Comment
from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {'text': 'Текст записи',
                  'group': 'Название группы',
                  'image': 'Изображение'}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {'text': 'Текст комментария'}
