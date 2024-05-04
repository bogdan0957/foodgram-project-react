from django.db import models
from django.core.validators import MinValueValidator
from users.models import User


class Tag(models.Model):
    name = models.CharField(max_length=200)
    color = models.CharField(max_length=7)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=200)

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'


class RecipeList(models.Model):
    tags = models.ForeignKey(Tag, on_delete=models.CASCADE, verbose_name='Список тегов')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Автор')
    ingredients = models.ForeignKey(Ingredient, on_delete=models.CASCADE, verbose_name='Список ингредиентов')
    is_favorited = models.BooleanField(verbose_name='Находится ли в избранном')
    is_in_shopping_cart = models.BooleanField(verbose_name='Находится ли в корзине')
    name = models.CharField('Название', max_length=200)
    # image = models.('Ссылка на картинку на сайте')
    text = models.TextField('Описание')
    cooking_time = models.IntegerField('Время приготовления (в минутах)', validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'


class IngredientRecipe(models.Model):
    recipe = models.ForeignKey(RecipeList, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = 'Ингридиент для рецепта'
        verbose_name_plural = 'Ингридиенты для рецепта'

