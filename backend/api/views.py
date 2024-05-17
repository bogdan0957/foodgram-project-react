"""
ViewSets.
"""
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticatedOrReadOnly,
                                        IsAuthenticated)
from rest_framework.response import Response

from recipes.models import (Recipe, Ingredient, Tag, Favorite,
                            ShoppingCart, IngredientRecipe)
from users.models import User, Follow
from .filters import IngredientSearchFilter, RecipeFilter
from .pagination import LimitPagination
from .permissions import IsAuthorOrAuthOrReadOnly
from .serializers import (RecipelistSerializer, IngredientSerializer,
                          TagSerializer, FavoriteSerializer,
                          UserCreateSerializer, RecipeCreateSerializer,
                          FollowSerializer, ShoppingCartSerializer,
                          FollowMakeSerializer)


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для рецептов."""
    serializer_class = RecipelistSerializer
    permission_classes = [IsAuthorOrAuthOrReadOnly]
    pagination_class = LimitPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list'):
            return RecipelistSerializer
        return RecipeCreateSerializer

    def get_queryset(self):
        return Recipe.objects.all().prefetch_related(
            'tags').select_related('author')

    def add_recipe_favorite_or_shopping_card(self, request, pk, serializers):
        serializer = serializers(
            data={'user': request.user.id,
                  'recipe': pk}, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_recipe_favorite_or_shopping_card(self, request, pk, model):
        recipe = get_object_or_404(Recipe, pk=pk)
        object = model.objects.filter(user=request.user, recipe=recipe)
        if object.exists():
            object.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        if request.method == 'POST':
            return self.add_recipe_favorite_or_shopping_card(
                request, pk, FavoriteSerializer
            )
        return self.delete_recipe_favorite_or_shopping_card(
            request, pk, Favorite
        )

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            return self.add_recipe_favorite_or_shopping_card(
                request, pk, ShoppingCartSerializer
            )
        return self.delete_recipe_favorite_or_shopping_card(
            request, pk, ShoppingCart
        )

    @action(detail=False, methods=('get',),
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        purchases = (
            IngredientRecipe.objects.filter(
                recipe__shopping_cart__user=self.request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(amount=Sum('amount'))
        )
        ingredient_list = [
            'Список необходимых ингредиентов:',
        ]
        for el in purchases:
            ingredient_list.append(
                f' • {el["ingredient__name"]}: {el["amount"]} '
                f'{el["ingredient__measurement_unit"]}'
            )
        file = '\n'.join(ingredient_list)

        response = HttpResponse(file, content_type='text/plain')
        response[
            'Content-Disposition'
        ] = 'attachment; filename=IngredientList.txt'

        return response


class UserCreateAndSubscribeViewSet(UserViewSet):
    """ViewSet для Кастомного Пользователя."""
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    pagination_class = LimitPagination
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        subscriptions = User.objects.filter(following__user=self.request.user)
        page = self.paginate_queryset(subscriptions)
        serializer = FollowSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id):
        if request.method == 'POST':
            serializer = FollowMakeSerializer(
                data={'user': request.user.id,
                      'following': get_object_or_404(User, pk=id).id})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        following = get_object_or_404(User, pk=id)
        object = Follow.objects.filter(user=request.user, following=following)
        if object.exists():
            object.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для Ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = [IngredientSearchFilter]
    search_fields = ('^name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для Тэгов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = [IsAuthenticatedOrReadOnly]
