from django_filters.rest_framework import FilterSet, filters
from django_filters.rest_framework import filters
from rest_framework.filters import SearchFilter

from recipes.models import Ingredient, RecipeList, Tag
from users.models import User


class IngredientSearchFilter(SearchFilter):
    search_param = 'name'

    class Meta:
        model = Ingredient
        fields = ('name', )


class TagFilter(FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )

    class Meta:
        model = RecipeList
        fields = ('tags', 'author',)