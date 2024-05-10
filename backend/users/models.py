"""
Модели.
"""
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    """Кастомная модель пользователя."""
    username = models.CharField(
        'Уникальный юзернейм',
        max_length=150,
        unique=True
    )
    email = models.EmailField(
        'Адрес электронной почты',
        max_length=254,
        unique=True
    )
    first_name = models.CharField(
        'Имя',
        max_length=150
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=150
    )
    password = models.CharField(
        'Пароль',
        max_length=150
    )

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'

    def str(self):
        return self.username


class Follow(models.Model):
    """Модель отслеживания."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'

    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('user',)

    def clean(self):
        if self.user == self.following:
            raise ValidationError('Вы не можете подписаться на себя.')
