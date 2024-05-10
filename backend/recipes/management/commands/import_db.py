"""
Команда для импорта ингредиентов в базу данных.
"""
import json
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from recipes.models import Ingredient


class Command(BaseCommand):
    BASE_DIR = settings.BASE_DIR

    def handle(self, *args, **options):
        try:
            path = self.BASE_DIR / 'data/ingredients.json'
            with open(path, 'r', encoding='utf-8-sig') as file:
                data = json.load(file)
                for item in data:
                    Ingredient.objects.get_or_create(**item)
        except CommandError as error:
            raise CommandError from error
        self.stdout.write(self.style.SUCCESS(
            'База данных ingredient пополненна'
        ))
