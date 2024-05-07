from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from djoser.views import UserViewSet
from datetime import date

from typing_extensions import Self

from users.models import User
from recipes.models import RecipeList, Ingredient, Tag
from .serializers import (RecipelistSerializer, IngredientSerializer,
                          TagSerializer, UserGetSerializer,
                          UserCreateSerializer, RecipeForSerializer,
                          RecipesBriefSerializer, FollowSerializer)
from .filters import IngredientSearchFilter, TagFilter
from .pagination import Pagination


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = RecipeList.objects.all()
    serializer_class = RecipelistSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = LimitOffsetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = TagFilter
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action in ('list'):
            return RecipelistSerializer
        else:
            return RecipeForSerializer

    def get_queryset(self):
        queryset = RecipeList.objects.all().prefetch_related(
            'tags', 'ingredients').select_related('author')
        return queryset

    # def perform_create(self, serializer):
    #     serializer.save(author=self.request.user)
    #     self.request.user.save()



class UserCustomViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    @action(detail=False,
            methods=['get'],
            url_path='subscriptions',
            permission_classes=[IsAuthenticated])
    def subscriptions(self: Self, request: Request):
        user = request.user
        subscriptions = User.objects.filter(following__user=user)
        page = self.paginate_queryset(subscriptions)
        serializer = FollowSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = [IngredientSearchFilter]
    search_fields = ('^name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = [IsAuthenticatedOrReadOnly]












