"""
Адресация.
"""
from django.urls import include, path, re_path
from rest_framework.routers import SimpleRouter

from api.views import (RecipeViewSet, UserCustomViewSet,
                       IngredientViewSet, TagViewSet)

router_v1 = SimpleRouter()
router_v1.register('recipes', RecipeViewSet, basename='recipes')
router_v1.register('users', UserCustomViewSet, basename='users')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')
router_v1.register('tags', TagViewSet, basename='tags')


urlpatterns = [
    path('v1/auth/', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.authtoken')),
    path('', include(router_v1.urls))
]
