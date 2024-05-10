"""
Сериализаторы.
"""
import base64

from django.core.files.base import ContentFile
from django.core.validators import MaxLengthValidator, RegexValidator
from django.db import transaction
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from recipes.models import (RecipeList, Ingredient, Tag,
                            IngredientRecipe, Favorites,
                            ShoppingCart)
from users.models import User, Follow


class Base64ImageField(serializers.ImageField):
    """Сериализатор для изображений."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class IngredientForRecipe(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = (
            'id', 'amount',
        )

    def validate_id(self, value):
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                "Ингредиент с данным id не существует."
            )
        return value


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для Ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тэгов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для Пользователя."""
    email = serializers.EmailField(
        validators=[
            UniqueValidator(queryset=User.objects.all()),
            MaxLengthValidator(254,
                               message='Длина email не должна быть больше '
                                       'чем 254 символа.'
                               ),
        ],
    )
    username = serializers.CharField(
        validators=[
            UniqueValidator(queryset=User.objects.all()),
            RegexValidator(regex=r"^[\w.@+-]+$", ),
            MaxLengthValidator(
                150,
                message='Длина username не должна быть '
                        'больше чем 254 символа.'),

        ]
    )
    password = serializers.CharField(
        write_only=True, required=True,
        alidators=[
            MaxLengthValidator(
                150,
                message='Длина пароля не должна'
                        'превышать 150'
                        'символов.'
            ),
        ],

    )

    class Meta:
        model = User
        fields = (
            'email', 'username', 'first_name', 'last_name', 'id', 'password'
        )
        write_only_fields = ('password',)

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserGetSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed',
                  )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and request.user.follower.filter(user=obj).exists()
        )


class ViewRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = RecipeList
        fields = ['id', 'name', 'image', 'cooking_time']


class FollowSerializer(UserGetSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='recipes.count')

    class Meta(UserGetSerializer.Meta):
        fields = UserGetSerializer.Meta.fields + (
            "recipes",
            "recipes_count",
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return None
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit is not None:
            recipes = obj.recipes.all()[:int(recipes_limit)]
        else:
            recipes = obj.recipes.all()
        serializer = ViewRecipeSerializer(
            recipes,
            many=True
        )
        return serializer.data

    def get_recipes_count(self, obj):
        return RecipeList.objects.filter(author=obj.author).count()


class FollowMakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ('user', 'following')

    def validate(self, attrs):
        user = attrs['user']
        following = attrs['following']

        if user.follower.filter(following=following).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на данного автора.'
            )
        if user == following:
            raise serializers.ValidationError(
                'Вы не можете подписаться на себя!'
            )
        return attrs

    def to_representation(self, instance):
        return FollowSerializer(
            instance.following,
            context={'request': self.context.get('request')}
        ).data


class RecipeIngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredients.id')
    name = serializers.ReadOnlyField(source='ingredients.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredients.measurement_unit'
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipelistSerializer(serializers.ModelSerializer):
    author = UserGetSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = RecipeIngredientAmountSerializer(many=True,
                                                   source='ingredientrecipes')
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = RecipeList
        fields = (
            'id', 'ingredients', 'tags', 'image', 'author', 'is_favorited',
            'name', 'text', 'cooking_time', 'is_in_shopping_cart'
        )

    def get_is_favorited(self, obj):
        if self.context['request'] is None or (
                self.context['request'].user.is_anonymous
        ):
            return False
        user = self.context['request'].user
        is_favorited = obj.favorites.filter(user=user).exists()
        return is_favorited

    def get_is_in_shopping_cart(self, obj):
        if self.context['request'] is None or (
                self.context['request'].user.is_anonymous
        ):
            return False
        user = self.context['request'].user
        is_in_shopping_cart = obj.shopping_cart.filter(user=user).exists()
        return is_in_shopping_cart


class RecipeForSerializer(serializers.ModelSerializer):
    ingredients = IngredientForRecipe(many=True)
    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )

    class Meta:
        model = RecipeList
        fields = (
            'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time',
        )

    def validate_ingredients(self, data):
        ingredients = self.initial_data.get('ingredients')
        ingredients_array = []
        if not ingredients:
            raise serializers.ValidationError(
                'Поле обязательное к заполнению.'
            )
        for ingredient in ingredients:
            if ingredient['id'] in ingredients_array:
                raise serializers.ValidationError(
                    'Ингредиенты не должны дублироваться.'
                )
            ingredients_array.append(ingredient['id'])
        return data

    def validate_tags(self, data):
        tags = self.initial_data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                'Поле обязательное к заполнению.'
            )
        if len(tags) == 1:
            return data
        duplicate = False
        for el in tags:
            if tags.count(el) > 1:
                duplicate = True
        if duplicate:
            raise serializers.ValidationError(
                'Тэги не должны повторятся.'
            )
        else:
            return data

    def main(self, data_ing, recipe):
        ingredients = []
        for el in data_ing:
            amount = el['amount']
            ingredient_id = el['id']
            ingredients.append(
                IngredientRecipe(
                    ingredients=Ingredient.objects.get(
                        id=ingredient_id
                    ),
                    recipes=recipe,
                    amount=amount
                ),
            )
        IngredientRecipe.objects.bulk_create(ingredients)

    @transaction.atomic
    def create(self, validated_data):
        data_ing = validated_data.pop('ingredients')
        data_tags = validated_data.pop('tags')
        author = self.context.get('request').user
        recipes = RecipeList.objects.create(author=author, **validated_data)
        self.main(data_ing, recipes)
        recipes.tags.set(data_tags)
        recipes.save()
        return recipes

    @transaction.atomic
    def update(self, instance, validated_data):
        if 'ingredients' in validated_data:
            ingredients_data = validated_data.pop('ingredients')
        else:
            raise serializers.ValidationError(
                'Поле ingredients отсутствует!'
            )
        if 'tags' in validated_data:
            tags_data = validated_data.pop('tags')
        else:
            raise serializers.ValidationError(
                'Поле tags отсутствует!'
            )
        instance.tags.clear()
        instance.tags.set(tags_data)
        instance.ingredients.clear()
        self.main(
            ingredients_data,
            recipe=instance,
        )
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        serializer = RecipelistSerializer(
            instance,
            context={'request': self.context.get('request')},
        )
        return serializer.data


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorites
        fields = '__all__'

    def validate(self, attrs):
        recipe = attrs['recipe']
        user = attrs['user']
        obj = user.favorites.filter(recipe=recipe)
        if self.context['request'].method == 'POST':
            if obj.exists():
                raise serializers.ValidationError('Уже в избранном!')
        if self.context['request'].method == 'DELETE':
            if not obj.exists():
                raise serializers.ValidationError('Рецепта нет в избранном')
        return attrs

    def to_representation(self, instance):
        serializer = ViewRecipeSerializer(
            instance.recipe, context={'request': self.context.get('request')}
        )
        return serializer.data


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = '__all__'

    def validate(self, attrs):
        recipe = attrs['recipe']
        user = attrs['user']
        obj = user.shopping_cart.filter(recipe=recipe)
        if self.context['request'].method == 'POST':
            if obj.exists():
                raise serializers.ValidationError('Уже в корзине!')
        if self.context['request'].method == 'DELETE':
            if not obj.exists():
                raise serializers.ValidationError('Нет в корзине')
        return attrs

    def to_representation(self, instance):
        serializer = ViewRecipeSerializer(
            instance.recipe, context={'request': self.context.get('request')}
        )
        return serializer.data
