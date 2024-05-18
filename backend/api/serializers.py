"""
Сериализаторы.
"""
import base64

from django.core.files.base import ContentFile
from django.core.validators import (MaxLengthValidator, RegexValidator)
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
        if data < constants.INGREDIENTRECIPE_AMOUNT_MIN:
            raise serializers.ValidationError(
                f'Количество ингредиентов не может быть меньше '
                f'{constants.INGREDIENTRECIPE_AMOUNT_MIN}.'
            )
        if data > constants.INGREDIENTRECIPE_AMOUNT_MAX:
            raise serializers.ValidationError(
                f'Количество ингредиентов не может быть больше '
                f'{constants.INGREDIENTRECIPE_AMOUNT_MAX}.'
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
            RegexValidator(regex=r'^[\w.@+-]+$', ),
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
            'recipes',
            'recipes_count',
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
                    'Передано не значение, запрос принимает только число!'
                    'Неправильные данные: "один", "два" и т.д.,'
                    'Правильные данные: 1, 2, "2", "1" и т.д.'
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

    def check_for_a_duplicate(self, data, variable, text):
        object = self.initial_data.get(variable)
        if (len(object)
                == constants.MIN_NUMBER_OF_TAGS_AND_INGREDIENT_IN_RECIPE):
            return data
        is_duplicate = False
        for el in object:
            if (object.count(el)
                    > constants.MIN_NUMBER_OF_TAGS_AND_INGREDIENT_IN_RECIPE):
                is_duplicate = True
        if is_duplicate:
            raise serializers.ValidationError(
                text
            )
        return data

    def validate_ingredients(self, data):
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                'Поле обязательное к заполнению.'
            )
        return self.check_for_a_duplicate(
            data, 'ingredients',
            'Ингридиенты не должны повторяться'
        )

    def validate_tags(self, data):
        tags = self.initial_data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                'Поле обязательное к заполнению.'
            )
        return self.check_for_a_duplicate(
            data, 'tags',
            'Тэги не должны дублироваться'
        )

    def validate_cooking_time(self, data):
        if data < constants.RECIPE_COOKING_TIME_MIN:
            raise serializers.ValidationError(
                f'Время приготовления не может быть меньше '
                f'{constants.RECIPE_COOKING_TIME_MIN} мин.'
            )
        elif data > constants.RECIPE_COOKING_TIME_MAX:
            raise serializers.ValidationError(
                f'Время приготовления не может быть больше '
                f'{constants.RECIPE_COOKING_TIME_MAX} мин.'
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


class FavoriteAndShoppingCardSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('user', 'recipe')

    def to_representation(self, instance):
        serializer = ViewRecipeSerializer(
            instance.recipe, context={'request': self.context.get('request')}
        )
        return serializer.data

    def validate(self, data):
        if self.Meta.model.objects.filter(
                user=data.get('user'), recipe=data.get('recipe')
        ).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен'
            )
        return data


class FavoriteSerializer(FavoriteAndShoppingCardSerializer):
    class Meta(FavoriteAndShoppingCardSerializer.Meta):
        model = Favorite


class ShoppingCartSerializer(FavoriteAndShoppingCardSerializer):
    class Meta(FavoriteAndShoppingCardSerializer.Meta):
        model = ShoppingCart
