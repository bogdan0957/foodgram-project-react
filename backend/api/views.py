from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from djoser.views import UserViewSet


from users.models import User, Follow
from recipes.models import RecipeList, Ingredient, Tag
from .serializers import (RecipelistSerializer, IngredientSerializer,
                          TagSerializer,
                          UserCreateSerializer, RecipeForSerializer,
                          FollowSerializer,
                          FollowMakeSerializer)
from .filters import IngredientSearchFilter, TagFilter
from .permissions import IsAuthorOrAuthOrReadOnly


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = RecipeList.objects.all()
    serializer_class = RecipelistSerializer
    permission_classes = [IsAuthorOrAuthOrReadOnly]
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
            serializer = get_object_or_404(Follow, user=user, following=following)
            serializer.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

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
