"""
Модели.
"""
from django.core.validators import MinValueValidator, MaxValueValidator, \
    RegexValidator
from django.db import models
from django.db.models import UniqueConstraint

from backend import constants
from users.models import User


class Tag(models.Model):
    """Модель тэгов."""
    name = models.CharField(max_length=constants.TAG_NAME_MAX_LENGHT,
                            unique=True)
    color = models.CharField(
        max_length=constants.TAG_COLOR_MAX_LENGHT,
        unique=True,
        validators=[
            RegexValidator(
                regex='^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
            )
        ])
    slug = models.SlugField(max_length=constants.TAG_SLUG_MAX_LENGHT,
                            unique=True)

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиентов."""
    name = models.CharField(max_length=constants.INGREDIENT_NAME_MAX_LENGHT)
    measurement_unit = models.CharField(
        max_length=constants.INGREDIENT_MEASUREMENT_MAX_LENGHT
    )

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        constraints = [
            UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""
    tags = models.ManyToManyField(Tag, verbose_name='Список тегов',
                                  related_name='recipes')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               verbose_name='Автор', related_name='recipes')
    ingredients = models.ManyToManyField(Ingredient,
                                         verbose_name='Список ингредиентов',
                                         related_name='recipes')
    name = models.CharField(max_length=constants.RECIPE_NAME_MAX_LENGHT,
                            verbose_name='recipes')
    image = models.ImageField('Изображение',
                              upload_to='recipes/images')
    text = models.TextField('Описание')
    cooking_time = models.PositiveIntegerField(
        'Время приготовления (в минутах)',
        validators=[MinValueValidator(1), MaxValueValidator(100)])
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    """Модель ингредиентов в рецепте."""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='ingredientrecipes')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                   related_name='ingredientrecipes')
    amount = models.SmallIntegerField('Количество',
                                      validators=[MaxValueValidator(1000),
                                                  MinValueValidator(1)])

    class Meta:
        verbose_name = 'Ингридиент для рецепта'
        verbose_name_plural = 'Ингридиенты для рецепта'


class RecipeTag(models.Model):
    """Модель M2M связи Тэгов и Рецепта."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE)
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'tag'], name='recipetag_unique')]


class Favorites(models.Model):
    """Модель отслеживания."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт')
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь')

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные"
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'user'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил "{self.recipe}" в Избранное'


class ShoppingCart(models.Model):
    """Модель списка продуктов."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт')
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь')

    class Meta:
        verbose_name = "Список продуктов"
        verbose_name_plural = "Списки продуктов"
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'user'],
                name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил "{self.recipe}" в Список продуктов'
