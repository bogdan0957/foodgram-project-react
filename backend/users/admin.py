"""
Админ-зона для Пользователя.
"""
from django.contrib import admin

from users.models import User, Follow
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

admin.site.unregister(Group)


@admin.register(User)
class UserOrAdmin(DjangoUserAdmin):
    list_display = ('id',
                    'username',
                    'email',
                    'first_name',
                    'last_name'
                    )
    search_fields = ('username', 'first_name', 'last_name',)
    list_display_links = ('username',)
    verbose_name = 'Пользователи'


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'following')
    search_fields = ('user', 'following')
    list_display_links = ('user',)
    verbose_name = 'Отслеживание'
