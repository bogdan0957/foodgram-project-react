import base64

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.validators import MaxLengthValidator, RegexValidator
from django.db import transaction
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer
from rest_framework import serializers, status
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator

from users.models import User, Follow
from recipes.models import RecipeList, Ingredient, Tag, IngredientRecipe


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeList
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id',)


class IngredientForRecipe(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = (
            'id', 'amount'
        )

    def validate_id(self, value):
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                "Ингредиент с данным id не существует."
            )
        return value


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class UserCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[
            UniqueValidator(queryset=User.objects.all()),
            MaxLengthValidator(
                254,
                message=(f"Длина email не должна"
                         f"превышать 254 символа.")
            ),
        ],
    )
    username = serializers.CharField(
        validators=[
            UniqueValidator(queryset=User.objects.all()),
            RegexValidator(regex=r"^[\w.@+-]+$", ),
            MaxLengthValidator(150),
        ]
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[
            MaxLengthValidator(
                150,
                message=f"Длина пароля не должна"
                        f"превышать 150"
                        f"символов."
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
        user = self.context['request'].user
        if user.is_authenticated:
            return Follow.objects.filter(user=user, author=obj).exists()
        else:
            return False


class SubscriptionListSerializer(UserGetSerializer):
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return Follow.objects.filter(user=user,
                                     author=obj.author).exists()

    def get_recipes(self, obj):
        recipes = RecipeList.objects.filter(author=obj.author)
        return RecipeMinifiedSerializer(recipes, many=True,
                                        context=self.context).data

    def get_recipes_count(self, obj):
        return RecipeList.objects.filter(author=obj.author).count()


class NotDetailRecipeSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)

    class Meta:
        model = RecipeList
        fields = ['id', 'name', 'image', 'cooking_time']


class FollowSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField(source="author.email")
    id = serializers.ReadOnlyField(source="author.id")
    username = serializers.ReadOnlyField(source="author.username")
    first_name = serializers.ReadOnlyField(source="author.first_name")
    last_name = serializers.ReadOnlyField(source="author.last_name")
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = [
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        ]

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.GET.get('recipes_limit')
        queryset = RecipeList.objects.filter(author=obj.author)
        if recipes_limit:
            queryset = queryset[:int(recipes_limit)]
        return FollowSerializer(queryset, many=True).data


class FollowMakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ('user', 'author')

    def validate(self, attrs):
        user = attrs['user']
        author = attrs['author']

        if user.author.filter(author=author).exists():
           raise serializers.ValidationError(
               'Подписан'
           )
        return attrs

class RecipelistSerializer(serializers.ModelSerializer):
    author = UserGetSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = IngredientForRecipe(many=True)
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
        queryset=Tag.objects.all(),
        many=True
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
                'Поле обязательное к заполнению'
            )
        for ingredient in ingredients:
            if ingredient['id'] in ingredients_array:
                raise serializers.ValidationError({
                    'ingredient': 'Ингредиенты не дублируются'
                })
            ingredients_array.append(ingredient['id'])
        return data

    def validate_tags(self, data):
        tags = self.initial_data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                'Поле обязательное к заполнению!'
            )
        if len(tags) == 1:
            return data
        duplicate = False
        for el in tags:
            if tags.count(el) > 1:
                duplicate = True
        if duplicate:
            raise serializers.ValidationError(
                'Тэги не должны повторятся'
            )
        else:
            return data

    def create_and_update_logic(self, ingredients_data, recipe):
        recipe_ingredients = []
        for ingredient_data in ingredients_data:
            amount = ingredient_data['amount']
            ingredient_id = ingredient_data['id']
            recipe_ingredients.append(
                IngredientRecipe(
                    ingredients=Ingredient.objects.get(
                        id=ingredient_id
                    ),
                    recipes=recipe,
                    amount=amount
                ),
            )
        IngredientRecipe.objects.bulk_create(recipe_ingredients)

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        author = self.context.get('request').user
        recipe = RecipeList.objects.create(author=author, **validated_data)
        self.create_and_update_logic(ingredients_data, recipe)
        recipe.tags.set(tags_data)
        recipe.save()
        return recipe

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
        self.create_and_update_logic(
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


class RecipesBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeList
        fields = ('id', 'name', 'image', 'cooking_time')
