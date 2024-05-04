from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from djoser.views import UserViewSet
from datetime import date

from users.models import User
from recipes.models import RecipeList, Ingredient, Tag
from .serializers import RecipelistSerializer, IngredientSerializer, TagSerializer, UserGetSerializer, UserCreateSerializer
from .filters import IngredientSearchFilter

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = RecipeList.objects.all()
    serializer_class = RecipelistSerializer


class UserCustomViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    pagination_class = LimitOffsetPagination
    lookup_field = 'username'
    search_fields = ('username',)
    http_method_names = ['get', 'post', 'patch', 'delete']
    # permission_classes = ('AllowAny',)

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    # def get_serializer_class(self):
    #     if self.action == 'create':
    #         return UserCreateSerializer
    #     return UserGetSerializer
    #
    # def get_subscribed_recipes(self, user):
    #     subscribed_users = user.following.all()
    #     subscribed_recipes = RecipeList.objects.filter(
    #         author__in=subscribed_users,
    #         pub_date__lte=date.today())
    #     return subscribed_recipes
    #
    # def paginate_and_serialize(self, queryset):
    #     page = self.paginate_queryset(queryset)
    #     if page is not None:
    #         serializer = self.get_serializer(
    #             page, many=True,
    #             context={'request': self.request})
    #         return self.get_paginated_response(serializer.data)
    #
    #     serializer = self.get_serializer(
    #         queryset, many=True,
    #         context={'request': self.request})
    #     return Response(serializer.data)
    #
    # def list(self, request, *args, **kwargs):
    #     is_subscribed = request.query_params.get('is_subscribed', False)
    #
    #     if is_subscribed:
    #         user = request.user
    #         queryset = User.objects.prefetch_related(
    #             'recipes').filter(subscriptions__user=user)
    #     else:
    #         queryset = User.objects.prefetch_related('recipes')
    #
    #     return self.paginate_and_serialize(queryset)


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












