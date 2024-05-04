from django.conf import settings
from django.core.validators import MaxLengthValidator, RegexValidator
from djoser.serializers import UserSerializer
from rest_framework import serializers, status
from rest_framework import serializers
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator

from users.models import User, Follow
from recipes.models import RecipeList, Ingredient, Tag


class RecipelistSerializer(serializers.ModelSerializer):

    class Meta:
        model = RecipeList
        fields = '__all__'


class RecipeMinifiedSerializer(serializers.ModelSerializer):

    class Meta:
        model = RecipeList
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id',)


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


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ('user', 'author',)
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'author'),
                message='Подписка уже существует.'
            )
        ]
