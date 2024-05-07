# from django.contrib import admin
# from .models import (Ingredient, Tag, RecipeList, IngredientRecipe)
#
#
# # class IngredientInline(admin.StackedInline):
# #     model = IngredientRecipe
# #     extra = 1
# #     min_num = 1
#
#
# @admin.register(RecipeList)
# class RecipeAdmin(admin.ModelAdmin):
#     list_display = (
#         'id',
#         'name',
#         'author'
#     )
#     list_filter = (
#         'author',
#         'name',
#         'tags',
#     )
#     inlines = [IngredientInline]
#
#
# @admin.register(Ingredient)
# class IngredientAdmin(admin.ModelAdmin):
#     list_display = ('name', 'measurement_unit')
#     list_filter = ('measurement_unit',)
#     search_fields = ('name',)
#
#
# @admin.register(Tag)
# class TagAdmin(admin.ModelAdmin):
#     list_display = ('name', 'color', 'slug')
#     list_filter = ('name', 'color')
#     search_fields = ('name',)


