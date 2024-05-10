"""
Фильтры для поисков.
"""
from django_filters import ModelMultipleChoiceFilter
from django_filters.rest_framework import FilterSet
from django_filters.rest_framework import filters
from rest_framework.filters import SearchFilter

from recipes.models import Ingredient, RecipeList, Tag
from users.models import User


class IngredientSearchFilter(SearchFilter):
    """Фильтр для поиска по полю 'name' в IngredientViewSet."""
    search_param = 'name'

    class Meta:
        model = Ingredient
        fields = ('name', )


class RecipeFilter(FilterSet):
    """
    Фильтр для поиска по полю 'is_favorited', 'is_in_shopping_cart',
    'author', 'tags' в RecipeViewSet.
    """
    is_favorited = filters.BooleanFilter(method="favorited_method")
    is_in_shopping_cart = filters.BooleanFilter(
        method="in_shopping_cart_method"
    )
    author = filters.ModelChoiceFilter(queryset=User.objects.all())
    tags = ModelMultipleChoiceFilter(
        field_name="tags__slug",
        to_field_name="slug",
        queryset=Tag.objects.all(),
    )

    def favorited_method(self, queryset, name, value):

        if value and self.request.user.is_authenticated:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def in_shopping_cart_method(self, queryset, name, value):

        if value and self.request.user.is_authenticated:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset

    class Meta:
        model = RecipeList
        fields = ("author", "tags")

