"""
Сериализаторы.
"""
import base64

from django.core.files.base import ContentFile
from django.core.validators import (MaxLengthValidator, RegexValidator,
                                    MinValueValidator, MaxValueValidator)
from django.db import transaction
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from backend import constants
from recipes.models import (Recipe, Ingredient, Tag,
                            IngredientRecipe, Favorite,
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


class WriteIngredientInRecipe(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientRecipe
        fields = (
            'id', 'amount',
        )

    def validate_amount(self, data):
        if data < constants.INGREDIENTRECIPE_AMOUNT_MIN_VALIDATOR:
            raise serializers.ValidationError(
                'Количество ингредиентов не может быть меньше 1.'
            )
        elif data > constants.INGREDIENTRECIPE_AMOUNT_MAX_VALIDATOR:
            raise serializers.ValidationError(
                'Количество ингредиентов не может быть больше 1000.'
            )

        return data


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
            MaxLengthValidator(constants.USER_EMAIL_MAX_LENGHT,
                               message=f'Длина email не должна быть больше '
                                       f'чем {constants.USER_EMAIL_MAX_LENGHT}'
                                       f'символа.'
                               ),
        ],
    )
    username = serializers.CharField(
        validators=[
            UniqueValidator(queryset=User.objects.all()),
            RegexValidator(regex=r"^[\w.@+-]+$", ),
            MaxLengthValidator(
                constants.USER_USERNAME_MAX_LENGHT,
                message=f'Длина username не должна быть '
                        f'больше чем {constants.USER_USERNAME_MAX_LENGHT} '
                        f'символа.'),

        ]
    )
    password = serializers.CharField(
        write_only=True, required=True,
        validators=[
            MaxLengthValidator(
                constants.USER_PASSWORD_MAX_LENGHT,
                message=f'Длина пароля не должна'
                        f'превышать {constants.USER_PASSWORD_MAX_LENGHT}'
                        f'символов.'
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
        return (request
                and request.user.is_authenticated
                and request.user.follower.filter(user=obj).exists()
                )


class ViewRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
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
        recipes = obj.recipes.all()
        if not request or request.user.is_anonymous:
            return None
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit is not None:
            try:
                int(recipes_limit)
            except ValueError:
                raise ValueError(
                    'Передано не значение'
                )
            else:
                recipes = recipes[:int(recipes_limit)]
        else:
            recipes = recipes
        serializer = ViewRecipeSerializer(
            recipes,
            many=True
        )
        return serializer.data


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
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
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
        model = Recipe
        fields = (
            'id', 'ingredients', 'tags', 'image', 'author', 'is_favorited',
            'name', 'text', 'cooking_time', 'is_in_shopping_cart'
        )

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if self.context['request'] is None or (
                self.context['request'].user.is_anonymous
        ):
            return False
        return obj.favorites.filter(user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if self.context['request'] is None or (
                self.context['request'].user.is_anonymous
        ):
            return False
        return obj.shopping_cart.filter(user=user).exists()


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = WriteIngredientInRecipe(many=True)
    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time',
        )

    def validate_ingredients(self, data):
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                'Поле обязательное к заполнению.'
            )
        return data

    def validate_tags(self, data):
        tags = self.initial_data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                'Поле обязательное к заполнению.'
            )

        return data

    def validate(self, data):
        tags = self.initial_data.get('tags')
        if len(tags) == constants.INTEGER_FOR_NOT_DUPLICATE:
            return data
        is_duplicate_tags = False
        for el in tags:
            if tags.count(el) > constants.INTEGER_FOR_NOT_DUPLICATE:
                is_duplicate_tags = True
        if is_duplicate_tags:
            raise serializers.ValidationError(
                'Тэги не должны повторятся.'
            )
        ingredients = self.initial_data.get('ingredients')
        if len(ingredients) == constants.INTEGER_FOR_NOT_DUPLICATE:
            return data
        is_duplicate_ingredient = False
        for el3 in ingredients:
            if ingredients.count(el3) > constants.INTEGER_FOR_NOT_DUPLICATE:
                is_duplicate_ingredient = True
        if is_duplicate_ingredient:
            raise serializers.ValidationError(
                'Ингредиенты не должны повторятся.'
            )
        return data

    def validate_cooking_time(self, data):
        if data < constants.RECIPE_COOKING_TIME_MIN_VALIDATOR:
            raise serializers.ValidationError(
                'Время приготовления не может быть меньше 1 мин.'
            )
        elif data > constants.RECIPE_COOKING_TIME_MAX_VALIDATOR:
            raise serializers.ValidationError(
                'Время приготовления не может быть больше 100 мин.'
            )

        return data

    def create_ingredients(self, data_ing, recipe):
        IngredientRecipe.objects.bulk_create(
            IngredientRecipe(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )
            for ingredient in data_ing
        )

    @transaction.atomic
    def create(self, validated_data):
        data_ing = validated_data.pop('ingredients')
        data_tags = validated_data.pop('tags')
        author = self.context.get('request').user
        recipe = Recipe.objects.create(author=author, **validated_data)
        self.create_ingredients(data_ing, recipe)
        recipe.tags.set(data_tags)
        recipe.save()
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        IngredientRecipe.objects.filter(recipe=instance).delete()
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        instance.tags.clear()
        instance.tags.set(tags_data)
        self.create_ingredients(
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
        model = Favorite
        fields = ('user', 'recipe')

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
