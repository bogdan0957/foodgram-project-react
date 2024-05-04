from django.contrib import admin

from users.models import User


class UserAdmin(admin.ModelAdmin):
    """Представление модели User."""

    list_display = ('id',
                    'username',
                    'email',
                    'first_name',
                    'last_name'
                    )
    search_fields = ('username', 'first_name', 'last_name',)
    list_display_links = ('username',)
    verbose_name = 'Пользователи'


admin.site.register(User, UserAdmin)


