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
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response

from recipes.models import (RecipeList, Ingredient, Tag, Favorites,
                            ShoppingCart, IngredientRecipe)
from users.models import User
from .filters import IngredientSearchFilter, RecipeFilter
from .pagination import LimitPagination
from .permissions import IsAuthorOrAuthOrReadOnly
from .serializers import (RecipelistSerializer, IngredientSerializer,
                          TagSerializer, FavoriteSerializer,
                          UserCreateSerializer, RecipeForSerializer,
                          FollowSerializer, ShoppingCartSerializer,
                          FollowMakeSerializer)


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для рецептов."""
    queryset = RecipeList.objects.all()
    serializer_class = RecipelistSerializer
    permission_classes = [IsAuthorOrAuthOrReadOnly]
    pagination_class = LimitPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list'):
            return RecipelistSerializer
        else:
            return RecipeForSerializer

    def get_queryset(self):
        queryset = RecipeList.objects.all().prefetch_related(
            'tags', 'ingredients').select_related('author')
        return queryset

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        if request.method == 'POST':
            serializer = FavoriteSerializer(
                data={'user': request.user.id,
                      'recipe': pk}, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            get_object_or_404(Favorites, recipe_id=pk)
            favorite_with_empty_variable, _ = Favorites.objects.filter(
                user__id=request.user.id,
                recipe__id=pk
            ).delete()
            if favorite_with_empty_variable:
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk):
        user = request.user
        serializer = ShoppingCartSerializer(data={
            'user': user.id,
            'recipe': pk
        }, context={'request': request})
        if request.method == 'POST':
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            get_object_or_404(ShoppingCart, recipe_id=pk)
            shopping_cart_with_empty_variable, _ = ShoppingCart.objects.filter(
                user__id=request.user.id,
                recipe__id=pk
            ).delete()
            if shopping_cart_with_empty_variable:
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=("get",), permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = self.request.user
        purchases = (
            IngredientRecipe.objects.filter(recipes__shopping_cart__user=user)
            .values("ingredients")
            .annotate(amount=Sum("amount"))
        )
        ingredient_list = [
            "Список необходимых ингредиентов:",
        ]
        for el in purchases:
            ingredient = Ingredient.objects.get(pk=el["ingredients"])
            amount = el["amount"]
            ingredient_list.append(
                f" • {ingredient.name}: {amount} "
                f"{ingredient.measurement_unit}"
            )
        file = "\n".join(ingredient_list)

        response = HttpResponse(file, content_type="text/plain")
        response[
            "Content-Disposition"
        ] = "attachment; filename=IngredientList.txt"

        return response


class UserCustomViewSet(UserViewSet):
    """ViewSet для Кастомного Пользователя."""
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    pagination_class = LimitPagination
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        subscriptions = User.objects.filter(following__user=self.request.user)
        page = self.paginate_queryset(subscriptions)
        serializer = FollowSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def subscribe(self, request, id):
        user = request.user
        following = get_object_or_404(User, pk=id)
        if request.method == 'POST':
            serializer = FollowMakeSerializer(data={'user': user.id,
                                                    'following': following.id})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            follow_with_empty_variable, _ = user.follower.filter(
                following=following
            ).delete()
            if follow_with_empty_variable:
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
