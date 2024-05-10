"""
Пагинация.
"""
from rest_framework import pagination


class LimitPagination(pagination.PageNumberPagination):
    """Пагинация для RecipeViewSet, UserCustomViewSet."""
    page_size = 6
    page_size_query_param = 'limit'
