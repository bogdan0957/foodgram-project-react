from django.db import models
from django.core.validators import MinValueValidator
from users.models import User


class Tag(models.Model):
    name = models.CharField(max_length=200)
    color = models.CharField(max_length=7)
    slug = models.SlugField(max_length=200)


class Ingredient(models.Model):
    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=200)


class RecipeMinified(models.Model):
    name = models.CharField(max_length=200)
    # image = models.


class IngredientInRecipe(models.Model):
    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=200)
    amount = models.IntegerField(validators=[MinValueValidator(1)])


class RecipeList(models.Model):
    tags = models.ForeignKey(Tag, on_delete=models.CASCADE, verbose_name='Список тегов')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Автор')
    ingredients = models.ForeignKey(IngredientInRecipe, on_delete=models.CASCADE, verbose_name='Список ингредиентов')
    is_favorited = models.BooleanField(verbose_name='Находится ли в избранном')
    is_in_shopping_cart = models.BooleanField(verbose_name='Находится ли в корзине')
    name = models.CharField('Название', max_length=200)
    # image = models.('Ссылка на картинку на сайте')
    text = models.TextField('Описание')
    cooking_time = models.IntegerField('Время приготовления (в минутах)', validators=[MinValueValidator(1)])




