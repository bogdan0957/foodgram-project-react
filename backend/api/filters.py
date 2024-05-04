from django_filters.rest_framework import FilterSet
from django_filters.rest_framework import filters as djangofilters
from rest_framework.filters import SearchFilter

from recipes.models import Ingredient, RecipeList


class IngredientSearchFilter(SearchFilter):
    search_param = 'name'

    class Meta:
        model = Ingredient
        fields = ('name', )