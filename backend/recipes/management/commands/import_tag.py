"""
Команда для импорта тэгов в базу данных.
"""
import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from recipes.models import Tag


class Command(BaseCommand):
    BASE_DIR = settings.BASE_DIR

    def handle(self, *args, **options):
        try:
            path = self.BASE_DIR / 'data/tag.json'
            with open(path, 'r', encoding='utf-8-sig') as file:
                data = json.load(file)
                for item in data:
                    Tag.objects.get_or_create(**item)
        except CommandError as error:
            raise CommandError from error
        self.stdout.write(self.style.SUCCESS('База данных tag пополненна'))
