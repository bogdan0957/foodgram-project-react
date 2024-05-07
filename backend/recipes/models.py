from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import User


class Tag(models.Model):
    name = models.CharField(max_length=200, unique=True)
    color = models.CharField(max_length=7, unique=True)
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
        unique_together = ('name', 'measurement_unit',)

    def __str__(self):
        return self.name


class RecipeList(models.Model):
    tags = models.ManyToManyField(Tag, verbose_name='Список тегов', related_name='recipes')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Автор', related_name='recipes')
    ingredients = models.ManyToManyField(Ingredient, verbose_name='Список ингредиентов', related_name='recipes')
    name = models.CharField(max_length=200)
    image = models.ImageField('Изображение', upload_to='recipes/images')
    text = models.TextField('Описание')
    cooking_time = models.PositiveIntegerField('Время приготовления (в минутах)',
                                               validators=[MinValueValidator(1), MaxValueValidator(100)])
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    recipes = models.ForeignKey(RecipeList, on_delete=models.CASCADE, related_name='ingredientrecipes', )
    ingredients = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='ingredientrecipes')
    amount = models.PositiveSmallIntegerField('Количество', validators=[MaxValueValidator(1000),
                                                                        MinValueValidator(1)])

    class Meta:
        verbose_name = 'Ингридиент для рецепта'
        verbose_name_plural = 'Ингридиенты для рецепта'



class RecipeTag(models.Model):
    """Промежуточная модель для связи рецепта и тега."""
    recipe = models.ForeignKey(
        RecipeList,
        on_delete=models.CASCADE)
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'tag'], name='recipetag_unique')]


class Favorites(models.Model):
    """Модель избранного."""
    recipe = models.ForeignKey(
        RecipeList,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт')
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь')



class ShoppingCart(models.Model):
    """Модель продуктовой корзины."""
    recipe = models.ForeignKey(
        RecipeList,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт')
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'], name='usershoppingcart_unique')]

