"""
Модели.
"""
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

from backend import constants


class User(AbstractUser):
    """Кастомная модель пользователя."""
    username = models.CharField(
        'Уникальный юзернейм',
        max_length=constants.USER_USERNAME_MAX_LENGHT,
        unique=True
    )
    email = models.EmailField(
        'Адрес электронной почты',
        max_length=constants.USER_EMAIL_MAX_LENGHT,
        unique=True
    )
    first_name = models.CharField(
        'Имя',
        max_length=constants.USER_FIRST_NAME_MAX_LENGHT
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=constants.USER_LAST_NAME_MAX_LENGHT
    )
    password = models.CharField(
        'Пароль',
        max_length=constants.USER_PASSWORD_MAX_LENGHT
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

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
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'following'), name='unique_follow'
            )
        ]

    def clean(self):
        if self.user == self.following:
            raise ValidationError('Вы не можете подписаться на себя.')
